from dagster import execute_solid, file_relative_path, RunConfig, ModeDefinition, PipelineDefinition
from dagster_examples.airline_demo.pipelines import (
    define_airline_demo_ingest_pipeline,
    spark_session_local,
)
from dagster_examples.airline_demo.resources import create_airline_demo_spark_session
from dagster_examples.airline_demo.solids import process_q2_data


def load_csv(spark, relative_path):
    return (
        spark.read.format('csv')
        .options(header='true')
        .load(file_relative_path(__file__, relative_path))
    )


def get_process_q2_env_dict(subsample_pct):
    return {
        'solids': {'process_q2_data': {'config': {'subsample_pct': subsample_pct}}},
        'resources': {
            'db_info': {
                'config': {
                    'postgres_username': 'test',
                    'postgres_password': 'test',
                    'postgres_hostname': 'localhost',
                    'postgres_db_name': 'test',
                }
            }
        },
    }


def test_successful_process_q2_data(snapshot):
    spark = create_airline_demo_spark_session()

    april_data = load_csv(spark, 'april_data.csv')
    may_data = load_csv(spark, 'may_data.csv')
    june_data = load_csv(spark, 'june_data.csv')
    master_cord_data = load_csv(spark, 'master_cord_data.csv')

    result = execute_solid(
        define_airline_demo_ingest_pipeline(),
        'process_q2_data',
        inputs={
            'april_data': april_data,
            'may_data': may_data,
            'june_data': june_data,
            'master_cord_data': master_cord_data,
        },
        environment_dict=get_process_q2_env_dict(100),
        run_config=RunConfig(mode='local'),
    )

    assert result.success

    rows = result.transformed_value().collect()

    assert len(rows) == 80

    snapshot.assert_match(rows)


def test_successful_process_q2_data_with_empheral_pipeline(snapshot):
    spark = create_airline_demo_spark_session()

    april_data = load_csv(spark, 'april_data.csv')
    may_data = load_csv(spark, 'may_data.csv')
    june_data = load_csv(spark, 'june_data.csv')
    master_cord_data = load_csv(spark, 'master_cord_data.csv')

    result = execute_solid(
        PipelineDefinition(
            name='for_test',
            solids=[process_q2_data],
            mode_definitions=[ModeDefinition(resources={'spark': spark_session_local})],
        ),
        'process_q2_data',
        inputs={
            'april_data': april_data,
            'may_data': may_data,
            'june_data': june_data,
            'master_cord_data': master_cord_data,
        },
        environment_dict={'solids': {'process_q2_data': {'config': {'subsample_pct': 100}}}},
    )

    assert result.success

    rows = result.transformed_value().collect()

    assert len(rows) == 80

    snapshot.assert_match(rows)

