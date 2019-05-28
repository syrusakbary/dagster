import six

from dagster import check
from dagster.core.definitions import ExecutionTargetHandle
from dagster.utils import all_none


class CliUsageError(Exception):
    pass


def _cli_load_invariant(condition):
    if not condition:
        raise CliUsageError()


def handle_for_pipeline_cli_args(kwargs):
    '''Builds an ExecutionTargetHandle for CLI arguments, which can be any of the combinations
    for repo/pipeline loading above.
    '''
    check.dict_param(kwargs, 'kwargs')

    pipeline_name = kwargs.get('pipeline_name')

    if pipeline_name and not isinstance(pipeline_name, six.string_types):
        if len(pipeline_name) == 1:
            pipeline_name = pipeline_name[0]
        else:
            check.failed(
                'Can only handle zero or one pipeline args. Got {pipeline_name}'.format(
                    pipeline_name=repr(pipeline_name)
                )
            )

    # Pipeline from repository YAML and pipeline_name
    if pipeline_name and kwargs.get('module_name') is None and kwargs.get('python_file') is None:
        _cli_load_invariant(kwargs.get('fn_name') is None)
        return ExecutionTargetHandle.for_repo_yaml(
            repository_yaml=kwargs.get('repository_yaml') or 'repository.yml'
        ).with_pipeline_name(pipeline_name)

    # Pipeline from repository python file
    elif kwargs.get('python_file') and kwargs.get('fn_name') and pipeline_name:
        _cli_load_invariant(kwargs.get('repository_yaml') is None)
        _cli_load_invariant(kwargs.get('module_name') is None)
        return ExecutionTargetHandle.for_repo_python_file(
            python_file=kwargs['python_file'], fn_name=kwargs['fn_name']
        ).with_pipeline_name(pipeline_name)

    # Pipeline from repository module
    elif kwargs.get('module_name') and kwargs.get('fn_name') and pipeline_name:
        _cli_load_invariant(kwargs.get('repository_yaml') is None)
        _cli_load_invariant(kwargs.get('python_file') is None)
        return ExecutionTargetHandle.for_repo_module(
            module_name=kwargs['module_name'], fn_name=kwargs['fn_name']
        ).with_pipeline_name(pipeline_name)

    # Pipeline from pipeline python file
    elif kwargs.get('python_file') and kwargs.get('fn_name') and not pipeline_name:
        _cli_load_invariant(kwargs.get('repository_yaml') is None)
        _cli_load_invariant(kwargs.get('module_name') is None)
        return ExecutionTargetHandle.for_pipeline_python_file(
            python_file=kwargs['python_file'], fn_name=kwargs['fn_name']
        )

    # Pipeline from pipeline module
    elif kwargs.get('module_name') and kwargs.get('fn_name') and not pipeline_name:
        _cli_load_invariant(kwargs.get('repository_yaml') is None)
        _cli_load_invariant(kwargs.get('python_file') is None)
        return ExecutionTargetHandle.for_pipeline_module(
            module_name=kwargs['module_name'], fn_name=kwargs['fn_name']
        )
    else:
        raise CliUsageError()


def handle_for_repo_cli_args(kwargs):
    '''Builds an ExecutionTargetHandle for CLI arguments, which can be any of the combinations
    for repo loading above.
    '''
    check.dict_param(kwargs, 'kwargs')

    _cli_load_invariant(kwargs.get('pipeline_name') is None)

    if kwargs.get('repository_yaml') or all_none(kwargs):
        _cli_load_invariant(kwargs.get('module_name') is None)
        _cli_load_invariant(kwargs.get('python_file') is None)
        _cli_load_invariant(kwargs.get('fn_name') is None)
        return ExecutionTargetHandle.for_repo_yaml(
            repository_yaml=kwargs.get('repository_yaml') or 'repository.yml'
        )
    elif kwargs.get('module_name') and kwargs.get('fn_name'):
        _cli_load_invariant(kwargs.get('repository_yaml') is None)
        _cli_load_invariant(kwargs.get('python_file') is None)
        return ExecutionTargetHandle.for_repo_module(
            module_name=kwargs['module_name'], fn_name=kwargs['fn_name']
        )
    elif kwargs.get('python_file') and kwargs.get('fn_name'):
        _cli_load_invariant(kwargs.get('repository_yaml') is None)
        _cli_load_invariant(kwargs.get('module_name') is None)
        return ExecutionTargetHandle.for_repo_python_file(
            python_file=kwargs['python_file'], fn_name=kwargs['fn_name']
        )
    else:
        raise CliUsageError()
