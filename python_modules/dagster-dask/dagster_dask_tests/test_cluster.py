import os

from dagster import ExecutionTargetHandle, RunConfig, RunStorageMode
from dagster_dask import execute_on_dask, DaskConfig


def test_dask_cluster():
    result = execute_on_dask(
        ExecutionTargetHandle.for_pipeline_module(
            'dagster_examples.toys.hammer', 'define_hammer_pipeline'
        ),
        env_config={'storage': {'s3': {'s3_bucket': 'dagster-airflow-scratch'}}},
        run_config=RunConfig(storage_mode=RunStorageMode.S3),
        dask_config=DaskConfig(address='%s:8786' % os.getenv('DASK_ADDRESS')),
    )
    assert result.success
    assert result.result_for_solid('total').transformed_value() == 4
