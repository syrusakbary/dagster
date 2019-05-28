"""Type definitions for the airline_demo."""
import os

from collections import namedtuple
from io import BytesIO

import sqlalchemy

from pyspark.sql import DataFrame

from dagster import as_dagster_type, Dict, Field, String
from dagster.core.storage.runs import RunStorageMode
from dagster.core.storage.type_storage import TypeStoragePlugin
from dagster.core.types.runtime import Stringish, RuntimeType

from dagster_aws.s3.types import BytesIOS3StoragePlugin

AirlineDemoResources = namedtuple(
    'AirlineDemoResources',
    ('spark', 's3', 'db_url', 'db_engine', 'db_dialect', 'redshift_s3_temp_dir', 'db_load'),
)


class SparkDataFrameS3StoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def set_object(cls, intermediate_store, obj, _context, _runtime_type, paths):
        target_path = intermediate_store.object_store.key_for_paths(paths)
        obj.write.parquet(intermediate_store.uri_for_paths(paths, protocol='s3a://'))
        return target_path

    @classmethod
    def get_object(cls, intermediate_store, context, _runtime_type, paths):
        return context.resources.spark.read.parquet(
            intermediate_store.uri_for_paths(paths, protocol='s3a://')
        )


class SparkDataFrameFilesystemStoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def set_object(cls, intermediate_store, obj, _context, _runtime_type, paths):
        target_path = os.path.join(intermediate_store.root, *paths)
        obj.write.parquet(intermediate_store.uri_for_paths(paths))
        return target_path

    @classmethod
    def get_object(cls, intermediate_store, context, _runtime_type, paths):
        return context.resources.spark.read.parquet(os.path.join(intermediate_store.root, *paths))


SparkDataFrameType = as_dagster_type(
    DataFrame,
    name='SparkDataFrameType',
    description='A Pyspark data frame.',
    storage_plugins={
        RunStorageMode.S3: SparkDataFrameS3StoragePlugin,
        RunStorageMode.FILESYSTEM: SparkDataFrameFilesystemStoragePlugin,
    },
)


SqlAlchemyEngineType = as_dagster_type(
    sqlalchemy.engine.Connectable,
    name='SqlAlchemyEngineType',
    description='A SqlAlchemy Connectable',
)


class SqlTableName(Stringish):
    def __init__(self):
        super(SqlTableName, self).__init__(description='The name of a database table')


class FileFromPath(RuntimeType):
    def __init__(self):
        self.storage_plugins = {RunStorageMode.S3: BytesIOS3StoragePlugin}
        super(FileFromPath, self).__init__(
            'FileFromPath',
            'FileFromPath',
            description='Bytes representing the contents of a file at a specific path.',
        )

    def coerce_runtime_value(self, value):
        with open(value, 'rb') as fd:
            return BytesIO(fd.read())


RedshiftConfigData = Dict(
    {
        'redshift_username': Field(String),
        'redshift_password': Field(String),
        'redshift_hostname': Field(String),
        'redshift_db_name': Field(String),
        's3_temp_dir': Field(String),
    }
)


DbInfo = namedtuple('DbInfo', 'engine url jdbc_url dialect load_table')


PostgresConfigData = Dict(
    {
        'postgres_username': Field(String),
        'postgres_password': Field(String),
        'postgres_hostname': Field(String),
        'postgres_db_name': Field(String),
    }
)
