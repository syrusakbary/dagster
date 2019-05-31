import os
import pickle
import tempfile

import pytest

from dagster import execute_pipeline, PipelineDefinition, RunConfig

from dagstermill import DagstermillError, define_dagstermill_solid
from dagstermill.examples.repository import (
    define_add_pipeline,
    define_error_pipeline,
    define_hello_world_explicit_yield_pipeline,
    define_hello_world_pipeline,
    define_hello_world_with_output_pipeline,
    define_no_repo_registration_error_pipeline,
    define_resource_pipeline,
    define_resource_with_exception_pipeline,
    define_test_notebook_dag_pipeline,
    define_tutorial_pipeline,
)


def cleanup_result_notebook(result):
    if not result:
        return
    materializations = [
        x for x in result.step_event_list if x.event_type_value == 'STEP_MATERIALIZATION'
    ]
    for materialization in materializations:
        result_path = materialization.event_specific_data.materialization.path
        if os.path.exists(result_path):
            os.unlink(result_path)


def test_hello_world():
    result = None
    try:
        result = execute_pipeline(define_hello_world_pipeline())
        assert result.success
    finally:
        cleanup_result_notebook(result)


def test_hello_world_with_output():
    result = None
    try:
        pipeline = define_hello_world_with_output_pipeline()
        result = execute_pipeline(pipeline)
        assert result.success
        assert result.result_for_solid('hello_world_output').transformed_value() == 'hello, world'
    finally:
        cleanup_result_notebook(result)


def test_hello_world_explicit_yield():
    result = None
    try:
        result = execute_pipeline(define_hello_world_explicit_yield_pipeline())
        materializations = [
            x for x in result.event_list if x.event_type_value == 'STEP_MATERIALIZATION'
        ]
        assert len(materializations) == 2
        assert materializations[0].event_specific_data.materialization.path.startswith(
            '/tmp/dagstermill/'
        )
        assert materializations[1].event_specific_data.materialization.path == '/path/to/file'
    finally:
        cleanup_result_notebook(result)


def test_add_pipeline():
    result = None
    try:
        pipeline = define_add_pipeline()
        result = execute_pipeline(
            pipeline, {'loggers': {'console': {'config': {'log_level': 'ERROR'}}}}
        )
        assert result.success
        assert result.result_for_solid('add_two_numbers').transformed_value() == 3
    finally:
        cleanup_result_notebook(result)


def test_notebook_dag():
    result = None
    try:
        result = execute_pipeline(
            define_test_notebook_dag_pipeline(),
            environment_dict={'solids': {'load_a': {'config': 1}, 'load_b': {'config': 2}}},
        )
        assert result.success
        assert result.result_for_solid('add_two').transformed_value() == 3
        assert result.result_for_solid('mult_two').transformed_value() == 6
    finally:
        cleanup_result_notebook(result)


def test_error_notebook():
    result = None
    try:
        with pytest.raises(
            DagstermillError, match='Error occurred during the execution of Dagstermill solid'
        ) as exc:
            execute_pipeline(define_error_pipeline())
        assert 'Someone set up us the bomb' in exc.value.original_exc_info[1].args[0]
        result = execute_pipeline(
            define_error_pipeline(), run_config=RunConfig.nonthrowing_in_process()
        )
        assert not result.success
        assert result.step_event_list[1].event_type.value == 'STEP_FAILURE'
    finally:
        cleanup_result_notebook(result)


def test_tutorial_pipeline():
    result = None
    try:
        pipeline = define_tutorial_pipeline()
        result = execute_pipeline(
            pipeline, {'loggers': {'console': {'config': {'log_level': 'DEBUG'}}}}
        )
        assert result.success
    finally:
        cleanup_result_notebook(result)


def test_no_repo_registration_error():
    result = None
    try:
        with pytest.raises(
            DagstermillError,
            match='Error occurred during the execution of Dagstermill solid no_repo_reg',
        ) as exc:
            execute_pipeline(define_no_repo_registration_error_pipeline())
        assert (
            'If Dagstermill solids have outputs that require serialization strategies'
            in exc.value.original_exc_info[1].args[0]
        )
        result = execute_pipeline(
            define_no_repo_registration_error_pipeline(),
            run_config=RunConfig.nonthrowing_in_process(),
        )
        assert not result.success
    finally:
        cleanup_result_notebook(result)


def test_hello_world_reexecution():
    result = None
    reexecution_result = None
    try:
        result = execute_pipeline(define_hello_world_pipeline())
        assert result.success

        output_notebook_path = [
            x for x in result.step_event_list if x.event_type_value == 'STEP_MATERIALIZATION'
        ][0].event_specific_data.materialization.path

        reexecution_solid = define_dagstermill_solid(
            'hello_world_reexecution', output_notebook_path
        )

        reexecution_pipeline = PipelineDefinition([reexecution_solid])

        reexecution_result = execute_pipeline(reexecution_pipeline)
        assert reexecution_result.success

    finally:
        cleanup_result_notebook(result)
        cleanup_result_notebook(reexecution_result)


def test_resources_notebook():
    result = None
    with tempfile.NamedTemporaryFile() as fd:
        path = fd.name

    try:
        result = execute_pipeline(
            define_resource_pipeline(), {'resources': {'list': {'config': path}}}
        )
        assert result.success

        # Expect something like:
        # ['e8d636: Opened', 'e8d636: Hello, solid!', '9d438e: Opened', '9d438e: Hello, notebook!',
        #  '9d438e: Closed', 'e8d636: Closed']
        with open(path, 'rb') as fd:
            messages = pickle.load(fd)

        messages = [message.split(': ') for message in messages]

        resource_ids = [x[0] for x in messages]
        assert len(set(resource_ids)) == 2
        assert resource_ids[0] == resource_ids[1] == resource_ids[5]
        assert resource_ids[2] == resource_ids[3] == resource_ids[4]

        msgs = [x[1] for x in messages]
        assert msgs[0] == msgs[2] == 'Opened'
        assert msgs[4] == msgs[5] == 'Closed'
        assert msgs[1] == 'Hello, solid!'
        assert msgs[3] == 'Hello, notebook!'

    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_resources_notebook_with_exception():
    result = None
    with tempfile.NamedTemporaryFile() as fd:
        path = fd.name

    try:
        result = execute_pipeline(
            define_resource_with_exception_pipeline(),
            {'resources': {'list': {'config': path}}},
            run_config=RunConfig.nonthrowing_in_process(),
        )
        assert not result.success
        assert result.step_event_list[4].event_type.value == 'STEP_FAILURE'
        assert 'raise Exception()' in result.step_event_list[4].event_specific_data.error.message

        # Expect something like:
        # ['e8d636: Opened', 'e8d636: Hello, solid!', '9d438e: Opened', '9d438e: Hello, notebook!',
        #  '9d438e: Closed', 'e8d636: Closed']
        with open(path, 'rb') as fd:
            messages = pickle.load(fd)

        messages = [message.split(': ') for message in messages]

        resource_ids = [x[0] for x in messages]
        assert len(set(resource_ids)) == 2
        assert resource_ids[0] == resource_ids[1] == resource_ids[5]
        assert resource_ids[2] == resource_ids[3] == resource_ids[4]

        msgs = [x[1] for x in messages]
        assert msgs[0] == msgs[2] == 'Opened'
        assert msgs[4] == msgs[5] == 'Closed'
        assert msgs[1] == 'Hello, solid!'
        assert msgs[3] == 'Hello, notebook!'

    finally:
        if os.path.exists(path):
            os.unlink(path)
