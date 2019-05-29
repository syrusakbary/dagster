import os

import pytest

from dagster import execute_pipeline
from dagster.utils import script_relative_path
from dagster.cli.pipeline import do_execute_command, print_pipeline
from dagster.core.errors import DagsterExecutionStepExecutionError

from dagster_pandas.examples.pandas_hello_world.pipeline import (
    define_pandas_hello_world_pipeline,
    define_failure_pipeline,
)


def test_pipeline_include():
    assert define_pandas_hello_world_pipeline()


def test_execute_pipeline():
    pipeline = define_pandas_hello_world_pipeline()
    environment = {
        'solids': {
            'sum_solid': {'inputs': {'num': {'csv': {'path': script_relative_path('num.csv')}}}}
        }
    }

    result = execute_pipeline(pipeline, environment_dict=environment)

    assert result.success

    assert result.result_for_solid('sum_solid').transformed_value().to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }

    assert result.result_for_solid('sum_sq_solid').transformed_value().to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_sq': [9, 49],
    }


def test_cli_execute():

    # currently paths in env files have to be relative to where the
    # script has launched so we have to simulate that
    cwd = os.getcwd()
    try:

        os.chdir(script_relative_path('../..'))

        do_execute_command(
            pipeline=define_pandas_hello_world_pipeline(),
            env_file_list=[
                script_relative_path('../../dagster_pandas/examples/pandas_hello_world/*.yaml')
            ],
            raise_on_error=True,
        )
    finally:
        # restore cwd
        os.chdir(cwd)


def test_cli_execute_failure():

    # currently paths in env files have to be relative to where the
    # script has launched so we have to simulate that
    with pytest.raises(DagsterExecutionStepExecutionError) as e_info:
        cwd = os.getcwd()
        try:

            os.chdir(script_relative_path('../..'))

            do_execute_command(
                pipeline=define_failure_pipeline(),
                env_file_list=[
                    script_relative_path('../../dagster_pandas/examples/pandas_hello_world/*.yaml')
                ],
                raise_on_error=True,
            )
        finally:
            # restore cwd
            os.chdir(cwd)
    assert 'I am a programmer and I make error' in str(e_info.value.__cause__)


def test_cli_print():
    print_pipeline(
        define_pandas_hello_world_pipeline(), full=False, print_fn=lambda *_args, **_kwargs: None
    )
    print_pipeline(
        define_pandas_hello_world_pipeline(), full=True, print_fn=lambda *_args, **_kwargs: None
    )
