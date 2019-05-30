"""Pipeline definitions for the airline_demo."""

from dagster import (
    DependencyDefinition,
    ModeDefinition,
    PipelineDefinition,
    PresetDefinition,
    SolidInstance,
    file_relative_path,
)

from dagster_aws.s3.resources import s3_resource
from dagster_aws.s3.solids import download_from_s3_to_bytes, put_object_to_s3_bytes

from .resources import (
    postgres_db_info_resource,
    redshift_db_info_resource,
    spark_session_local,
    tempfile_resource,
)
from .solids import (
    average_sfo_outbound_avg_delays_by_destination,
    canonicalize_column_names,
    delays_by_geography,
    delays_vs_fares,
    delays_vs_fares_nb,
    eastbound_delays,
    ingest_csv_to_spark,
    load_data_to_database_from_spark,
    process_q2_data,
    process_sfo_weather_data,
    q2_sfo_outbound_flights,
    sfo_delays_by_destination,
    subsample_spark_dataset,
    tickets_with_destination,
    unzip_file,
    westbound_delays,
)


test_mode = ModeDefinition(
    name='test',
    resources={
        'spark': spark_session_local,
        'db_info': redshift_db_info_resource,
        'tempfile': tempfile_resource,
        's3': s3_resource,
    },
)


local_mode = ModeDefinition(
    name='local',
    resources={
        'spark': spark_session_local,
        's3': s3_resource,
        'db_info': postgres_db_info_resource,
        'tempfile': tempfile_resource,
    },
)


prod_mode = ModeDefinition(
    name='prod',
    resources={
        'spark': spark_session_local,  # FIXME
        's3': s3_resource,
        'db_info': redshift_db_info_resource,
        'tempfile': tempfile_resource,
    },
)


def define_airline_demo_ingest_pipeline():
    solids = [
        canonicalize_column_names,
        download_from_s3_to_bytes,
        ingest_csv_to_spark,
        load_data_to_database_from_spark,
        process_q2_data,
        process_sfo_weather_data,
        subsample_spark_dataset,
        unzip_file,
    ]
    dependencies = {
        SolidInstance('download_from_s3_to_bytes', alias='download_april_on_time_data'): {},
        SolidInstance('download_from_s3_to_bytes', alias='download_may_on_time_data'): {},
        SolidInstance('download_from_s3_to_bytes', alias='download_june_on_time_data'): {},
        SolidInstance('download_from_s3_to_bytes', alias='download_master_cord_data'): {},
        SolidInstance('download_from_s3_to_bytes', alias='download_q2_coupon_data'): {},
        SolidInstance('download_from_s3_to_bytes', alias='download_q2_market_data'): {},
        SolidInstance('download_from_s3_to_bytes', alias='download_q2_ticket_data'): {},
        SolidInstance('download_from_s3_to_bytes', alias='download_q2_sfo_weather'): {},
        SolidInstance('unzip_file', alias='unzip_april_on_time_data'): {
            'archive_file': DependencyDefinition('download_april_on_time_data')
        },
        SolidInstance('unzip_file', alias='unzip_may_on_time_data'): {
            'archive_file': DependencyDefinition('download_may_on_time_data')
        },
        SolidInstance('unzip_file', alias='unzip_june_on_time_data'): {
            'archive_file': DependencyDefinition('download_june_on_time_data')
        },
        SolidInstance('unzip_file', alias='unzip_master_cord_data'): {
            'archive_file': DependencyDefinition('download_master_cord_data')
        },
        SolidInstance('unzip_file', alias='unzip_q2_coupon_data'): {
            'archive_file': DependencyDefinition('download_q2_coupon_data')
        },
        SolidInstance('unzip_file', alias='unzip_q2_market_data'): {
            'archive_file': DependencyDefinition('download_q2_market_data')
        },
        SolidInstance('unzip_file', alias='unzip_q2_ticket_data'): {
            'archive_file': DependencyDefinition('download_q2_ticket_data')
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_april_on_time_data'): {
            'input_csv_file': DependencyDefinition('unzip_april_on_time_data')
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_may_on_time_data'): {
            'input_csv_file': DependencyDefinition('unzip_may_on_time_data')
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_june_on_time_data'): {
            'input_csv_file': DependencyDefinition('unzip_june_on_time_data')
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_sfo_weather'): {
            'input_csv_file': DependencyDefinition('download_q2_sfo_weather')
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_coupon_data'): {
            'input_csv_file': DependencyDefinition('unzip_q2_coupon_data')
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_market_data'): {
            'input_csv_file': DependencyDefinition('unzip_q2_market_data')
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_q2_ticket_data'): {
            'input_csv_file': DependencyDefinition('unzip_q2_ticket_data')
        },
        SolidInstance('ingest_csv_to_spark', alias='ingest_master_cord_data'): {
            'input_csv_file': DependencyDefinition('unzip_master_cord_data')
        },
        'process_q2_data': {
            'april_data': DependencyDefinition('ingest_april_on_time_data'),
            'may_data': DependencyDefinition('ingest_may_on_time_data'),
            'june_data': DependencyDefinition('ingest_june_on_time_data'),
            'master_cord_data': DependencyDefinition('ingest_master_cord_data'),
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_q2_ticket_data'): {
            'data_frame': DependencyDefinition('ingest_q2_ticket_data')
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_q2_market_data'): {
            'data_frame': DependencyDefinition('ingest_q2_market_data')
        },
        SolidInstance('subsample_spark_dataset', alias='subsample_q2_coupon_data'): {
            'data_frame': DependencyDefinition('ingest_q2_coupon_data')
        },
        'process_sfo_weather_data': {
            'sfo_weather_data': DependencyDefinition('ingest_q2_sfo_weather')
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_coupon_data'): {
            'data_frame': DependencyDefinition('subsample_q2_coupon_data')
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_market_data'): {
            'data_frame': DependencyDefinition('subsample_q2_market_data')
        },
        SolidInstance('canonicalize_column_names', alias='canonicalize_q2_ticket_data'): {
            'data_frame': DependencyDefinition('subsample_q2_ticket_data')
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_on_time_data'): {
            'data_frame': DependencyDefinition('process_q2_data')
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_coupon_data'): {
            'data_frame': DependencyDefinition('canonicalize_q2_coupon_data')
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_market_data'): {
            'data_frame': DependencyDefinition('canonicalize_q2_market_data')
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_ticket_data'): {
            'data_frame': DependencyDefinition('canonicalize_q2_ticket_data')
        },
        SolidInstance('load_data_to_database_from_spark', alias='load_q2_sfo_weather'): {
            'data_frame': DependencyDefinition('process_sfo_weather_data')
        },
    }

    return PipelineDefinition(
        name="airline_demo_ingest_pipeline",
        solids=solids,
        dependencies=dependencies,
        mode_definitions=[test_mode, local_mode, prod_mode],
        preset_definitions=[
            PresetDefinition(
                name='local_fast',
                mode='local',
                environment_files=[
                    file_relative_path(__file__, 'environments/local_base.yaml'),
                    file_relative_path(__file__, 'environments/local_fast_ingest.yaml'),
                ],
            ),
            PresetDefinition(
                name='local_full',
                mode='local',
                environment_files=[
                    file_relative_path(__file__, 'environments/local_base.yaml'),
                    file_relative_path(__file__, 'environments/local_full_ingest.yaml'),
                ],
            ),
        ],
    )


def define_airline_demo_warehouse_pipeline():
    return PipelineDefinition(
        name="airline_demo_warehouse_pipeline",
        solids=[
            average_sfo_outbound_avg_delays_by_destination,
            delays_by_geography,
            delays_vs_fares,
            delays_vs_fares_nb,
            eastbound_delays,
            q2_sfo_outbound_flights,
            sfo_delays_by_destination,
            tickets_with_destination,
            put_object_to_s3_bytes,
            westbound_delays,
        ],
        dependencies={
            'q2_sfo_outbound_flights': {},
            'tickets_with_destination': {},
            'westbound_delays': {},
            'eastbound_delays': {},
            'average_sfo_outbound_avg_delays_by_destination': {
                'q2_sfo_outbound_flights': DependencyDefinition('q2_sfo_outbound_flights')
            },
            'delays_vs_fares': {
                'tickets_with_destination': DependencyDefinition('tickets_with_destination'),
                'average_sfo_outbound_avg_delays_by_destination': DependencyDefinition(
                    'average_sfo_outbound_avg_delays_by_destination'
                ),
            },
            'fares_vs_delays': {'table_name': DependencyDefinition('delays_vs_fares')},
            'sfo_delays_by_destination': {
                'table_name': DependencyDefinition('average_sfo_outbound_avg_delays_by_destination')
            },
            'delays_by_geography': {
                'eastbound_delays': DependencyDefinition('eastbound_delays'),
                'westbound_delays': DependencyDefinition('westbound_delays'),
            },
            SolidInstance('put_object_to_s3_bytes', alias='upload_outbound_avg_delay_pdf_plots'): {
                'file_obj': DependencyDefinition('sfo_delays_by_destination')
            },
            SolidInstance('put_object_to_s3_bytes', alias='upload_delays_vs_fares_pdf_plots'): {
                'file_obj': DependencyDefinition('fares_vs_delays')
            },
            SolidInstance('put_object_to_s3_bytes', alias='upload_delays_by_geography_pdf_plots'): {
                'file_obj': DependencyDefinition('delays_by_geography')
            },
        },
        mode_definitions=[test_mode, local_mode, prod_mode],
        preset_definitions=[
            PresetDefinition(
                name='local',
                mode='local',
                environment_files=[
                    file_relative_path(__file__, 'environments/local_base.yaml'),
                    file_relative_path(__file__, 'environments/local_warehouse.yaml'),
                ],
            )
        ],
    )
