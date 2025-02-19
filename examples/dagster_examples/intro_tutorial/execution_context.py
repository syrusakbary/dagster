from dagster import PipelineDefinition, execute_pipeline, solid


@solid
def debug_message(context):
    context.log.debug('A debug message.')
    return 'foo'


@solid
def error_message(context):
    context.log.error('An error occurred.')


def define_execution_context_pipeline():
    return PipelineDefinition(
        name='execution_context_pipeline', solids=[debug_message, error_message]
    )


if __name__ == '__main__':
    execute_pipeline(
        define_execution_context_pipeline(),
        {'loggers': {'console': {'config': {'log_level': 'DEBUG'}}}},
    )
