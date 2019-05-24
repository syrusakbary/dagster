from dagster import ExecutionTargetHandle
from dagster.utils import script_relative_path
from dagit.app import create_app, notebook_view

from dagster_graphql.implementation.pipeline_run_storage import (
    InMemoryPipelineRun,
    PipelineRunStorage,
)


def test_create_app():
    handle = ExecutionTargetHandle.for_repo_yaml(script_relative_path('./repository.yml'))
    pipeline_run_storage = PipelineRunStorage(create_pipeline_run=InMemoryPipelineRun)
    assert create_app(handle, pipeline_run_storage, use_synchronous_execution_manager=True)
    assert create_app(handle, pipeline_run_storage, use_synchronous_execution_manager=False)


def test_notebook_view():
    notebook_path = script_relative_path('render_uuid_notebook.ipynb')
    html_response, code = notebook_view(notebook_path)
    assert '6cac0c38-2c97-49ca-887c-4ac43f141213' in html_response
    assert code == 200
