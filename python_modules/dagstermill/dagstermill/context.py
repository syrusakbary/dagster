from dagster import check
from dagster.core.definitions.resource import ResourcesBuilder
from dagster.core.errors import DagsterResourceFunctionError
from dagster.core.execution.context_creation_pipeline import (
    _create_resource_fn_lambda,
    user_code_context_manager,
)
from dagster.core.execution.context.system import (
    SystemPipelineExecutionContext,
    SystemPipelineExecutionContextData,
)
from dagster.core.execution.context.transform import AbstractTransformExecutionContext


class DagstermillInNotebookExecutionContext(AbstractTransformExecutionContext):
    def __init__(self, pipeline_context, out_of_pipeline=False):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        self._pipeline_context = pipeline_context
        self.out_of_pipeline = out_of_pipeline
        self._resource_context_stack = []

    def has_tag(self, key):
        return self._pipeline_context.has_tag(key)

    def get_tag(self, key):
        return self._pipeline_context.get_tag(key)

    @property
    def run_id(self):
        return self._pipeline_context.run_id

    @property
    def environment_dict(self):
        return self._pipeline_context.environment_dict

    @property
    def environment_config(self):
        return self._pipeline_context.environment_config

    @property
    def logging_tags(self):
        return self._pipeline_context.logging_tags

    @property
    def pipeline_def(self):
        return self._pipeline_context.pipeline_def

    @property
    def resources(self):
        return self._pipeline_context.resources

    @property
    def run_config(self):
        return self._pipeline_context.run_config

    @property
    def log(self):
        return self._pipeline_context.log

    @property
    def solid_def(self):
        if self.out_of_pipeline:
            check.failed('Cannot access solid_def in dagstermill exploratory context')

    @property
    def solid(self):
        if self.out_of_pipeline:
            check.failed('Cannot access solid in dagstermill exploratory context')

    def setup_resources(self):
        resources = {}
        mode_definition = self.pipeline_def.get_mode_definition(self.run_config.mode)

        # Basically, instead of a context manager we need to persist a stack on the context;
        # then in teardown_resources we will exit everything.
        for resource_name, resource_def in mode_definition.resource_defs.items():
            user_fn = _create_resource_fn_lambda(
                self.pipeline_def,
                resource_def,
                self.environment_config.resources.get(resource_name, {}).get('config'),
                self.run_config.run_id,
                self.log,
            )

            context_manager = user_code_context_manager(
                user_fn,
                DagsterResourceFunctionError,
                'Error executing resource_fn on ResourceDefinition {name}'.format(
                    name=resource_name
                ),
            )

            resource_obj = context_manager.__enter__()  # pylint: disable=no-member
            self._resource_context_stack.append(context_manager)

            resources[resource_name] = resource_obj

            # pylint: disable=protected-access
            self._pipeline_context._pipeline_context_data = SystemPipelineExecutionContextData(
                self.run_config,
                ResourcesBuilder(resources),
                self.environment_config,
                self.pipeline_def,
                self._pipeline_context.run_storage,
                self._pipeline_context.intermediates_manager,
            )

    def teardown_resources(self):
        for context_manager in reversed(self._resource_context_stack):
            context_manager.__exit__(None, None, None)
