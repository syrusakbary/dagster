import contextlib
import os
import shutil
import tempfile

from pyspark.sql import SparkSession

from dagster import resource, Field

from .types import DbInfo, PostgresConfigData, RedshiftConfigData
from .utils import (
    create_postgres_db_url,
    create_postgres_engine,
    create_redshift_db_url,
    create_redshift_engine,
)


def create_airline_demo_spark_session():
    return (
        SparkSession.builder.appName('AirlineDemo')
        .config(
            'spark.jars.packages',
            'com.databricks:spark-avro_2.11:3.0.0,'
            'com.databricks:spark-redshift_2.11:2.0.1,'
            'com.databricks:spark-csv_2.11:1.5.0,'
            'org.postgresql:postgresql:42.2.5,'
            'org.apache.hadoop:hadoop-aws:2.6.5,'
            'com.amazonaws:aws-java-sdk:1.7.4',
        )
        .getOrCreate()
    )


@resource
def spark_session_local(_init_context):
    # Need two versions of this, one for test/local and one with a
    # configurable cluster
    return create_airline_demo_spark_session()


class TempfileManager(object):
    def __init__(self):
        self.paths = []
        self.files = []
        self.dirs = []

    def tempfile(self):
        temporary_file = tempfile.NamedTemporaryFile('w+b', delete=False)
        self.files.append(temporary_file)
        self.paths.append(temporary_file.name)
        return temporary_file

    def tempdir(self):
        temporary_directory = tempfile.mkdtemp()
        self.dirs.append(temporary_directory)
        return temporary_directory

    def close(self):
        for fobj in self.files:
            fobj.close()
        for path in self.paths:
            if os.path.exists(path):
                os.remove(path)
        for dir_ in self.dirs:
            shutil.rmtree(dir_)


@contextlib.contextmanager
def _tempfile_manager():
    manager = TempfileManager()
    try:
        yield manager
    finally:
        manager.close()


@resource
def tempfile_resource(_init_context):
    with _tempfile_manager() as manager:
        yield manager


@resource(config_field=Field(RedshiftConfigData))
def redshift_db_info_resource(init_context):
    db_url_jdbc = create_redshift_db_url(
        init_context.resource_config['redshift_username'],
        init_context.resource_config['redshift_password'],
        init_context.resource_config['redshift_hostname'],
        init_context.resource_config['redshift_db_name'],
    )

    db_url = create_redshift_db_url(
        init_context.resource_config['redshift_username'],
        init_context.resource_config['redshift_password'],
        init_context.resource_config['redshift_hostname'],
        init_context.resource_config['redshift_db_name'],
        jdbc=False,
    )

    s3_temp_dir = init_context.resource_config['s3_temp_dir']

    def _do_load(data_frame, table_name):
        data_frame.write.format('com.databricks.spark.redshift').option(
            'tempdir', s3_temp_dir
        ).mode('overwrite').jdbc(db_url_jdbc, table_name)

    return DbInfo(
        url=db_url,
        jdbc_url=db_url_jdbc,
        engine=create_redshift_engine(db_url),
        dialect='redshift',
        load_table=_do_load,
    )


@resource(config_field=Field(PostgresConfigData))
def postgres_db_info_resource(init_context):
    db_url_jdbc = create_postgres_db_url(
        init_context.resource_config['postgres_username'],
        init_context.resource_config['postgres_password'],
        init_context.resource_config['postgres_hostname'],
        init_context.resource_config['postgres_db_name'],
    )

    db_url = create_postgres_db_url(
        init_context.resource_config['postgres_username'],
        init_context.resource_config['postgres_password'],
        init_context.resource_config['postgres_hostname'],
        init_context.resource_config['postgres_db_name'],
        jdbc=False,
    )

    def _do_load(data_frame, table_name):
        data_frame.write.option('driver', 'org.postgresql.Driver').mode('overwrite').jdbc(
            db_url_jdbc, table_name
        )

    return DbInfo(
        url=db_url,
        jdbc_url=db_url_jdbc,
        engine=create_postgres_engine(db_url),
        dialect='postgres',
        load_table=_do_load,
    )


if __name__ == '__main__':
    # This is a brutal hack. When the SparkSession is created for the first time there is a lengthy
    # download process from Maven. This allows us to run python -m airline_demo.resources in the
    # Dockerfile and avoid a long runtime delay before each containerized solid executes.
    spark_session_local.resource_fn(None)
