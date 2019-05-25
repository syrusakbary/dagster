'''
This module contains the execution context objects that are internal to the system.
Not every property on these should be exposed to random Jane or Joe dagster user
so we have a different layer of objects that encode the explicit public API
in the user_context module
'''
from collections import namedtuple

from dagster import check
from dagster.utils import merge_dicts

from dagster.core.definitions.expectation import ExpectationDefinition
from dagster.core.definitions.input import InputDefinition
from dagster.core.definitions.output import OutputDefinition
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.runs import RunStorage
from dagster.core.system_config.objects import EnvironmentConfig

from ..config import RunConfig


class SystemPipelineExecutionContextData(
    namedtuple(
        '_SystemPipelineExecutionContextData',
        (
            'run_config resources environment_config pipeline_def '
            'run_storage intermediates_manager'
        ),
    )
):
    '''
    SystemPipelineExecutionContextData is the data that remains constant throughtout the entire
    execution of a pipeline.
    '''

    def __new__(
        cls,
        run_config,
        resources,
        environment_config,
        pipeline_def,
        run_storage,
        intermediates_manager,
    ):
        from dagster.core.definitions import PipelineDefinition
        from dagster.core.storage.intermediates_manager import IntermediatesManager

        return super(SystemPipelineExecutionContextData, cls).__new__(
            cls,
            run_config=check.inst_param(run_config, 'run_config', RunConfig),
            resources=resources,
            environment_config=check.inst_param(
                environment_config, 'environment_config', EnvironmentConfig
            ),
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            run_storage=check.inst_param(run_storage, 'run_storage', RunStorage),
            intermediates_manager=check.inst_param(
                intermediates_manager, 'intermediates_manager', IntermediatesManager
            ),
        )

    @property
    def run_id(self):
        return self.run_config.run_id

    @property
    def event_callback(self):
        return self.run_config.event_callback

    @property
    def environment_dict(self):
        return self.environment_config.original_config_dict


class SystemPipelineExecutionContext(object):
    __slots__ = [
        '_pipeline_context_data',
        '_logging_tags',
        '_log_manager',
        '_legacy_context',
        '_events',
    ]

    def __init__(self, pipeline_context_data, logging_tags, log_manager):
        self._pipeline_context_data = check.inst_param(
            pipeline_context_data, 'pipeline_context_data', SystemPipelineExecutionContextData
        )
        self._logging_tags = check.dict_param(logging_tags, 'logging_tags')
        self._log_manager = check.inst_param(log_manager, 'log_manager', DagsterLogManager)

    def for_step(self, step):
        from dagster.core.execution.plan.objects import ExecutionStep

        check.inst_param(step, 'step', ExecutionStep)

        logging_tags = merge_dicts(self.logging_tags, step.logging_tags)
        log_manager = DagsterLogManager(self.run_id, logging_tags, self.log.loggers)
        return SystemStepExecutionContext(
            self._pipeline_context_data, logging_tags, log_manager, step
        )

    @property
    def executor_config(self):
        return self.run_config.executor_config

    @property
    def run_config(self):
        return self._pipeline_context_data.run_config

    @property
    def resources(self):
        return self._pipeline_context_data.resources.build()

    @property
    def run_id(self):
        return self._pipeline_context_data.run_id

    @property
    def environment_dict(self):
        return self._pipeline_context_data.environment_dict

    @property
    def environment_config(self):
        return self._pipeline_context_data.environment_config

    @property
    def logging_tags(self):
        return self._logging_tags

    def has_tag(self, key):
        check.str_param(key, 'key')
        return key in self._logging_tags

    def get_tag(self, key):
        check.str_param(key, 'key')
        return self._logging_tags[key]

    @property
    def pipeline_def(self):
        return self._pipeline_context_data.pipeline_def

    @property
    def event_callback(self):
        return self._pipeline_context_data.event_callback

    def has_event_callback(self):
        return self._pipeline_context_data.event_callback is not None

    @property
    def log(self):
        return self._log_manager

    @property
    def run_storage(self):
        return self._pipeline_context_data.run_storage

    @property
    def intermediates_manager(self):
        return self._pipeline_context_data.intermediates_manager


class SystemStepExecutionContext(SystemPipelineExecutionContext):
    __slots__ = ['_step']

    def __init__(self, pipeline_context_data, tags, log_manager, step):
        from dagster.core.execution.plan.objects import ExecutionStep

        self._step = check.inst_param(step, 'step', ExecutionStep)
        super(SystemStepExecutionContext, self).__init__(pipeline_context_data, tags, log_manager)

    def for_transform(self):
        return SystemTransformExecutionContext(
            self._pipeline_context_data, self.logging_tags, self.log, self.step
        )

    def for_expectation(self, inout_def, expectation_def):
        return SystemExpectationExecutionContext(
            self._pipeline_context_data,
            self.logging_tags,
            self.log,
            self.step,
            inout_def,
            expectation_def,
        )

    @property
    def step(self):
        return self._step

    @property
    def solid_handle(self):
        return self._step.solid_handle

    @property
    def solid_def(self):
        return self.solid.definition

    @property
    def solid(self):
        return self.pipeline_def.get_solid(self._step.solid_handle)

    @property
    def resources(self):
        return self._pipeline_context_data.resources.build(
            self.solid.resource_mapper_fn, self.solid_def.resources
        )

    @property
    def mode(self):
        return self._pipeline_context_data.run_config.mode


class SystemTransformExecutionContext(SystemStepExecutionContext):
    @property
    def solid_config(self):
        solid_config = self.environment_config.solids.get(str(self.solid_handle))
        return solid_config.config if solid_config else None


class SystemExpectationExecutionContext(SystemStepExecutionContext):
    __slots__ = ['_inout_def', '_expectation_def']

    def __init__(self, pipeline_context_data, tags, log_manager, step, inout_def, expectation_def):
        self._expectation_def = check.inst_param(
            expectation_def, 'expectation_def', ExpectationDefinition
        )
        self._inout_def = check.inst_param(
            inout_def, 'inout_def', (InputDefinition, OutputDefinition)
        )
        super(SystemExpectationExecutionContext, self).__init__(
            pipeline_context_data, tags, log_manager, step
        )

    @property
    def expectation_def(self):
        return self._expectation_def

    @property
    def inout_def(self):
        return self._inout_def
