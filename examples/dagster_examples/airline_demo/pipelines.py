"""Pipeline definitions for the airline_demo."""

from dagster import ModeDefinition, PresetDefinition, file_relative_path
from dagster.core.definitions.pipeline import pipeline

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
    fares_vs_delays,
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
    @pipeline(
        # solids=[
        #     canonicalize_column_names,
        #     download_from_s3_to_bytes,
        #     ingest_csv_to_spark,
        #     load_data_to_database_from_spark,
        #     process_q2_data,
        #     process_sfo_weather_data,
        #     subsample_spark_dataset,
        #     unzip_file,
        # ],
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
    def airline_demo_ingest_pipeline():
        # pylint: disable=no-value-for-parameter
        return (
            dl_canonicalize_and_load('q2_coupon_data'),
            dl_canonicalize_and_load('q2_market_data'),
            dl_canonicalize_and_load('q2_ticket_data'),
            load_data_to_database_from_spark.alias('load_q2_on_time_data')(
                data_frame=process_q2_data(
                    april_data=dl_and_load_df('april_on_time'),
                    may_data=dl_and_load_df('may_on_time'),
                    june_data=dl_and_load_df('june_on_time'),
                    master_cord_data=dl_and_load_df('master_cord'),
                )
            ),
            load_data_to_database_from_spark.alias('load_q2_sfo_weather')(
                data_frame=process_sfo_weather_data(
                    sfo_weather_data=ingest_csv_to_spark.alias('ingest_q2_sfo_weather')(
                        input_csv_file=download_from_s3_to_bytes.alias('download_q2_sfo_weather')()
                    )
                )
            ),
        )

    return airline_demo_ingest_pipeline


def dl_and_load_df(label):
    def name(stage_name):
        return '{stage_name}_{label}_data'.format(stage_name=stage_name, label=label)

    return ingest_csv_to_spark.alias(name('ingest'))(
        input_csv_file=unzip_file.alias(name('unzip'))(
            archive_file=download_from_s3_to_bytes.alias(name('download'))()
        )
    )


# TODO, make into true composite?
def dl_canonicalize_and_load(segment_name):
    def seg(stage_name):
        return stage_name + '_' + segment_name

    return load_data_to_database_from_spark.alias(seg('load'))(
        data_frame=canonicalize_column_names.alias(seg('canonicalize'))(
            data_frame=subsample_spark_dataset.alias(seg('subsample'))(
                data_frame=ingest_csv_to_spark.alias(seg('ingest'))(
                    input_csv_file=unzip_file.alias(seg('unzip'))(
                        archive_file=download_from_s3_to_bytes.alias(seg('download'))()
                    )
                )
            )
        )
    )


def define_airline_demo_warehouse_pipeline():
    @pipeline(
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
    def airline_demo_warehouse_pipeline():
        average_delays = average_sfo_outbound_avg_delays_by_destination(
            q2_sfo_outbound_flights=q2_sfo_outbound_flights()
        )

        return (
            put_object_to_s3_bytes.alias('upload_delays_vs_fares_pdf_plots')(
                file_obj=fares_vs_delays(
                    table_name=delays_vs_fares(
                        tickets_with_destination=tickets_with_destination(),
                        average_sfo_outbound_avg_delays_by_destination=average_delays,
                    )
                )
            ),
            put_object_to_s3_bytes.alias('upload_outbound_avg_delay_pdf_plots')(
                file_obj=sfo_delays_by_destination(table_name=average_delays)
            ),
            put_object_to_s3_bytes.alias('upload_delays_by_geography_pdf_plots')(
                file_obj=delays_by_geography(
                    westbound_delays=westbound_delays(), eastbound_delays=eastbound_delays()
                )
            ),
        )

    return airline_demo_warehouse_pipeline
