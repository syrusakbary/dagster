import multiprocessing

from collections import namedtuple

from dagster import check
from dagster.utils import merge_dicts
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.storage.runs import RunStorageMode
from dagster.core.utils import make_new_run_id


class RunConfig(
    namedtuple(
        '_RunConfig',
        (
            'run_id tags event_callback loggers executor_config storage_mode reexecution_config '
            'step_keys_to_execute mode'
        ),
    )
):
    '''
    Configuration that controls the details of how Dagster will execute a pipeline.

    Args:
      run_id (str): The ID to use for this run. If not provided a new UUID will
        be created using `uuid4`.
      tags (dict[str, str]): Key value pairs that will be added to logs.
      event_callback (callable): A callback to invoke with each :py:class:`EventRecord`
        produced during execution.
      loggers (list): Additional loggers that log messages will be sent to.
      executor_config (ExecutorConfig): Configuration for where and how computation will occur.
      storage_mode (RunStorageMode): Where intermediate artifacts will be stored during execution.
      rexecution_config (RexecutionConfig): Information about a previous run to allow
        for subset rexecution.
      step_keys_to_execute (list[str]): They subset of steps from a pipeline to execute this run.
    '''

    def __new__(
        cls,
        run_id=None,
        tags=None,
        event_callback=None,
        loggers=None,
        executor_config=None,
        storage_mode=None,
        reexecution_config=None,
        step_keys_to_execute=None,
        mode=None,
    ):
        if (
            isinstance(executor_config, MultiprocessExecutorConfig)
            and storage_mode is RunStorageMode.IN_MEMORY
        ):
            raise DagsterInvariantViolationError(
                'Can not create a RunConfig with executor_config MultiProcessExecutorConfig and '
                'storage_mode RunStorageMode.IN_MEMORY'
            )

        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        return super(RunConfig, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id') if run_id else make_new_run_id(),
            tags=check.opt_dict_param(tags, 'tags', key_type=str, value_type=str),
            event_callback=check.opt_callable_param(event_callback, 'event_callback'),
            loggers=check.opt_list_param(loggers, 'loggers'),
            executor_config=check.inst_param(executor_config, 'executor_config', ExecutorConfig)
            if executor_config
            else InProcessExecutorConfig(),
            storage_mode=check.opt_inst_param(storage_mode, 'storage_mode', RunStorageMode),
            reexecution_config=check.opt_inst_param(
                reexecution_config, 'reexecution_config', ReexecutionConfig
            ),
            step_keys_to_execute=step_keys_to_execute,
            mode=check.opt_str_param(mode, 'mode'),
        )

    @staticmethod
    def nonthrowing_in_process():
        return RunConfig(executor_config=InProcessExecutorConfig(raise_on_error=False))

    def with_tags(self, **new_tags):
        new_tags = merge_dicts(self.tags, new_tags)
        return RunConfig(**merge_dicts(self._asdict(), {'tags': new_tags}))


class ExecutorConfig:
    pass


class InProcessExecutorConfig(ExecutorConfig):
    def __init__(self, raise_on_error=True):
        self.raise_on_error = check.bool_param(raise_on_error, 'raise_on_error')


class MultiprocessExecutorConfig(ExecutorConfig):
    def __init__(self, handle, max_concurrent=None):
        from dagster import ExecutionTargetHandle

        self.handle = check.inst_param(handle, 'handle', ExecutionTargetHandle)

        max_concurrent = (
            max_concurrent if max_concurrent is not None else multiprocessing.cpu_count()
        )
        self.max_concurrent = check.int_param(max_concurrent, 'max_concurrent')
        check.invariant(self.max_concurrent > 0, 'max_concurrent processes must be greater than 0')
        self.raise_on_error = False


class ReexecutionConfig:
    def __init__(self, previous_run_id, step_output_handles):
        self.previous_run_id = previous_run_id
        self.step_output_handles = step_output_handles
