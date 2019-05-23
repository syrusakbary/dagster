from dagster import execute_pipeline, ModeDefinition, PipelineDefinition
from dagster.utils.log import construct_single_handler_logger

from dagstermill.examples.repository import define_hello_logging_solid

from .test_logger import LogTestHandler


def test_logging():
    records = []

    pipeline_def = PipelineDefinition(
        name='hello_logging_pipeline',
        solids=[define_hello_logging_solid()],
        mode_definitions=[
            ModeDefinition(
                loggers={
                    'test': construct_single_handler_logger(
                        'test', 'debug', LogTestHandler(records)
                    )
                }
            )
        ],
    )

    execute_pipeline(pipeline_def, {'loggers': {'test': {}}})

    messages = [x.dagster_meta['orig_message'] for x in records]

    assert 'Hello, there!' in messages
