from dagster import (
    DagsterEventType,
    DependencyDefinition,
    InProcessExecutorConfig,
    ModeDefinition,
    PipelineDefinition,
    RunConfig,
    execute_pipeline,
    execute_solid,
    file_relative_path,
    solid,
)
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


def test_successful_process_q2_data_with_proper_context_handling():
    @solid
    def load_april_data(context):
        return load_csv(context.resources.spark, 'april_data.csv')

    @solid
    def load_may_data(context):
        return load_csv(context.resources.spark, 'may_data.csv')

    @solid
    def load_june_data(context):
        return load_csv(context.resources.spark, 'june_data.csv')

    @solid
    def load_master_cord_data(context):
        return load_csv(context.resources.spark, 'master_cord_data.csv')

    pipeline_result = execute_pipeline(
        PipelineDefinition(
            name='for_test',
            solids=[
                process_q2_data,
                load_april_data,
                load_may_data,
                load_june_data,
                load_master_cord_data,
            ],
            mode_definitions=[ModeDefinition(resources={'spark': spark_session_local})],
            dependencies={
                'process_q2_data': {
                    'april_data': DependencyDefinition('load_april_data'),
                    'may_data': DependencyDefinition('load_may_data'),
                    'june_data': DependencyDefinition('load_june_data'),
                    'master_cord_data': DependencyDefinition('load_master_cord_data'),
                }
            },
        ),
        environment_dict={'solids': {'process_q2_data': {'config': {'subsample_pct': 100}}}},
    )

    assert pipeline_result.success

    rows = pipeline_result.result_for_solid('process_q2_data').transformed_value().collect()

    assert len(rows) == 80


def test_successful_process_q2_data_with_proper_context_handling_subsample():
    @solid
    def load_april_data(context):
        return load_csv(context.resources.spark, 'april_data.csv')

    @solid
    def load_may_data(context):
        return load_csv(context.resources.spark, 'may_data.csv')

    @solid
    def load_june_data(context):
        return load_csv(context.resources.spark, 'june_data.csv')

    @solid
    def load_master_cord_data(context):
        return load_csv(context.resources.spark, 'master_cord_data.csv')

    pipeline_result = execute_pipeline(
        PipelineDefinition(
            name='for_sample_test',
            solids=[
                process_q2_data,
                load_april_data,
                load_may_data,
                load_june_data,
                load_master_cord_data,
            ],
            mode_definitions=[ModeDefinition(resources={'spark': spark_session_local})],
            dependencies={
                'process_q2_data': {
                    'april_data': DependencyDefinition('load_april_data'),
                    'may_data': DependencyDefinition('load_may_data'),
                    'june_data': DependencyDefinition('load_june_data'),
                    'master_cord_data': DependencyDefinition('load_master_cord_data'),
                }
            },
        ),
        environment_dict={'solids': {'process_q2_data': {'config': {'subsample_pct': 10}}}},
    )

    assert pipeline_result.success

    rows = pipeline_result.result_for_solid('process_q2_data').transformed_value().collect()

    assert len(rows) < 80


def test_missing_column_in_master_cord_data():
    @solid
    def load_april_data(context):
        return load_csv(context.resources.spark, 'april_data.csv')

    @solid
    def load_may_data(context):
        return load_csv(context.resources.spark, 'may_data.csv').drop('DestAirportSeqID')

    @solid
    def load_june_data(context):
        return load_csv(context.resources.spark, 'june_data.csv').drop('OriginAirportSeqID')

    @solid
    def load_master_cord_data(context):
        return load_csv(context.resources.spark, 'master_cord_data.csv')

    pipeline_result = execute_pipeline(
        PipelineDefinition(
            name='for_sample_test',
            solids=[
                process_q2_data,
                load_april_data,
                load_may_data,
                load_june_data,
                load_master_cord_data,
            ],
            mode_definitions=[ModeDefinition(resources={'spark': spark_session_local})],
            dependencies={
                'process_q2_data': {
                    'april_data': DependencyDefinition('load_april_data'),
                    'may_data': DependencyDefinition('load_may_data'),
                    'june_data': DependencyDefinition('load_june_data'),
                    'master_cord_data': DependencyDefinition('load_master_cord_data'),
                }
            },
        ),
        environment_dict={'solids': {'process_q2_data': {'config': {'subsample_pct': 100}}}},
        run_config=RunConfig(executor_config=InProcessExecutorConfig(raise_on_error=False)),
    )

    assert not pipeline_result.success

    solid_result = pipeline_result.result_for_solid('process_q2_data')

    assert not solid_result.success

    expectation_result = get_expectation_result_in_transform(solid_result, 'airport_ids_present')

    assert expectation_result.result_metadata['missing_columns'] == {
        'may': ['DestAirportSeqID'],
        'june': ['OriginAirportSeqID'],
    }


def get_expectation_result_in_transform(solid_result, expt_name):
    for step_event in solid_result.transforms:
        if (
            step_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT
            and step_event.event_specific_data.expectation_result.name == expt_name
        ):
            return step_event.event_specific_data.expectation_result

    raise Exception('not found')
