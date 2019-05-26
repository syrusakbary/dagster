"""Pipeline definitions for the airline_demo."""

import gzip
import os
import shutil

from dagster import (
    lambda_solid,
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    List,
    ModeDefinition,
    PipelineDefinition,
    SolidInstance,
    String,
)
from dagster.utils import safe_isfile, mkdir_p

from dagster_aws.s3.resources import s3_resource
from dagster_aws.s3.solids import download_from_s3_to_file
from dagster_snowflake import snowflake_resource, SnowflakeLoadSolidDefinition
from dagster_spark import SparkSolidDefinition


@lambda_solid(inputs=[InputDefinition('gzip_file', String)], output=OutputDefinition(List(String)))
def gunzipper(gzip_file):
    '''gunzips /path/to/foo.gz to /path/to/raw/2019/01/01/data.json
    '''
    # TODO: take date as an input

    path_prefix = os.path.dirname(gzip_file)
    output_folder = os.path.join(path_prefix, 'raw/2019/01/01')
    outfile = os.path.join(output_folder, 'data.json')

    if not safe_isfile(outfile):
        mkdir_p(output_folder)

        with gzip.open(gzip_file, 'rb') as f_in, open(outfile, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    return [path_prefix]


def define_event_ingest_pipeline():
    event_ingest = SparkSolidDefinition(
        name='event_ingest',
        main_class='io.dagster.events.EventPipeline',
        description='Ingest events from JSON to Parquet',
    )

    # TODO: express dependency of this solid on event_ingest
    snowflake_load = SnowflakeLoadSolidDefinition(
        'snowflake_load',
        # TODO: need to pull this out to a config
        src='file:///tmp/dagster/events/data/output/2019/01/01/*.parquet',
        table='events',
    )

    return PipelineDefinition(
        name='event_ingest_pipeline',
        solids=[download_from_s3_to_file, gunzipper, event_ingest, snowflake_load],
        dependencies={
            SolidInstance('gunzipper'): {
                'gzip_file': DependencyDefinition('download_from_s3_to_file')
            },
            SolidInstance('event_ingest'): {'spark_inputs': DependencyDefinition('gunzipper')},
            SolidInstance('snowflake_load'): {
                'start': DependencyDefinition('event_ingest', 'paths')
            },
        },
        mode_definitions=[
            ModeDefinition(resources={'s3': s3_resource, 'snowflake': snowflake_resource})
        ],
    )
