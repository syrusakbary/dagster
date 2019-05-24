from dagster import ExecutionTargetHandle
from dagster.utils import script_relative_path
from dagit.app import create_app

from dagster_graphql.implementation.pipeline_run_storage import (
    InMemoryPipelineRun,
    PipelineRunStorage,
)


def test_create_app():
    handle = ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yml'))
    pipeline_run_storage = PipelineRunStorage(create_pipeline_run=InMemoryPipelineRun)
    assert create_app(handle, pipeline_run_storage, use_synchronous_execution_manager=True)
    assert create_app(handle, pipeline_run_storage, use_synchronous_execution_manager=False)
