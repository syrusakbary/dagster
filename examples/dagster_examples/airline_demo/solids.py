'''A fully fleshed out demo dagster repository with many configurable options.'''

import os
import re
import zipfile

from io import BytesIO

from pyspark.sql import DataFrame
from sqlalchemy import text

from dagster import (
    Bytes,
    Dict,
    ExpectationResult,
    Field,
    InputDefinition,
    Int,
    OutputDefinition,
    Materialization,
    Result,
    SolidDefinition,
    String,
    check,
    solid,
)
from dagstermill import define_dagstermill_solid

from .types import FileFromPath, SparkDataFrameType, SqlTableName


PARQUET_SPECIAL_CHARACTERS = r'[ ,;{}()\n\t=]'


def _notebook_path(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notebooks', name)


def notebook_solid(name, notebook_path, inputs, outputs):
    return define_dagstermill_solid(name, _notebook_path(notebook_path), inputs, outputs)


# need a sql context w a sqlalchemy engine
def sql_solid(name, select_statement, materialization_strategy, table_name=None, inputs=None):
    '''Return a new solid that executes and materializes a SQL select statement.

    Args:
        name (str): The name of the new solid.
        select_statement (str): The select statement to execute.
        materialization_strategy (str): Must be 'table', the only currently supported
            materialization strategy. If 'table', the kwarg `table_name` must also be passed.
    Kwargs:
        table_name (str): THe name of the new table to create, if the materialization strategy
            is 'table'. Default: None.
        inputs (list[InputDefinition]): Inputs, if any, for the new solid. Default: None.

    Returns:
        function:
            The new SQL solid.
    '''
    inputs = check.opt_list_param(inputs, 'inputs', InputDefinition)

    materialization_strategy_output_types = {  # pylint:disable=C0103
        'table': SqlTableName,
        # 'view': String,
        # 'query': SqlAlchemyQueryType,
        # 'subquery': SqlAlchemySubqueryType,
        # 'result_proxy': SqlAlchemyResultProxyType,
        # could also materialize as a Pandas table, as a Spark table, as an intermediate file, etc.
    }

    if materialization_strategy not in materialization_strategy_output_types:
        raise Exception(
            'Invalid materialization strategy {materialization_strategy}, must '
            'be one of {materialization_strategies}'.format(
                materialization_strategy=materialization_strategy,
                materialization_strategies=str(list(materialization_strategy_output_types.keys())),
            )
        )

    if materialization_strategy == 'table':
        if table_name is None:
            raise Exception('Missing table_name: required for materialization strategy \'table\'')

    output_description = (
        'The string name of the new table created by the solid'
        if materialization_strategy == 'table'
        else 'The materialized SQL statement. If the materialization_strategy is '
        '\'table\', this is the string name of the new table created by the solid.'
    )

    description = '''This solid executes the following SQL statement:
    {select_statement}'''.format(
        select_statement=select_statement
    )

    # n.b., we will eventually want to make this resources key configurable
    sql_statement = (
        'drop table if exists {table_name};\n' 'create table {table_name} as {select_statement};'
    ).format(table_name=table_name, select_statement=select_statement)

    def compute_fn(context, _inputs):
        '''Inner function defining the new solid.

        Args:
            context (TransformExecutionContext): Must expose a `db` resource with an `execute` method,
                like a SQLAlchemy engine, that can execute raw SQL against a database.

        Returns:
            str:
                The table name of the newly materialized SQL select statement.
        '''

        context.log.info(
            'Executing sql statement:\n{sql_statement}'.format(sql_statement=sql_statement)
        )
        context.resources.db_info.engine.execute(text(sql_statement))
        yield Result(value=table_name, output_name='result')

    return SolidDefinition(
        name=name,
        inputs=inputs,
        outputs=[
            OutputDefinition(
                materialization_strategy_output_types[materialization_strategy],
                description=output_description,
            )
        ],
        compute_fn=compute_fn,
        description=description,
        metadata={'kind': 'sql', 'sql': sql_statement},
    )


@solid(
    name='unzip_file',
    inputs=[
        InputDefinition('archive_file', Bytes, description='The archive to unzip'),
        InputDefinition('archive_member', String, description='The archive member to extract.'),
    ],
    description='Extracts an archive member from a zip archive.',
    outputs=[OutputDefinition(Bytes, description='The unzipped archive member.')],
)
def unzip_file(_context, archive_file, archive_member):

    with zipfile.ZipFile(archive_file) as zip_ref:
        return BytesIO(zip_ref.open(archive_member).read())


def rename_spark_dataframe_columns(data_frame, fn):
    return data_frame.toDF(*[fn(c) for c in data_frame.columns])


@solid(
    name='ingest_csv_to_spark',
    inputs=[InputDefinition('input_csv_file', Bytes)],
    outputs=[OutputDefinition(SparkDataFrameType)],
)
def ingest_csv_to_spark(context, input_csv_file):
    tf = context.resources.tempfile.tempfile()
    with open(tf.name, 'wb') as fd:
        fd.write(input_csv_file.read())
    data_frame = (
        context.resources.spark.read.format('csv')
        .options(
            header='true',
            # inferSchema='true',
        )
        .load(tf.name)
    )

    # parquet compat
    return rename_spark_dataframe_columns(
        data_frame, lambda x: re.sub(PARQUET_SPECIAL_CHARACTERS, '', x)
    )


def do_prefix_column_names(df, prefix):
    check.inst_param(df, 'df', DataFrame)
    check.str_param(prefix, 'prefix')
    return rename_spark_dataframe_columns(df, lambda c: '{prefix}{c}'.format(prefix=prefix, c=c))


@solid(
    name='canonicalize_column_names',
    inputs=[
        InputDefinition(
            'data_frame', SparkDataFrameType, description='The data frame to canonicalize'
        )
    ],
    outputs=[OutputDefinition(SparkDataFrameType)],
)
def canonicalize_column_names(_context, data_frame):
    return rename_spark_dataframe_columns(data_frame, lambda c: c.lower())


def replace_values_spark(data_frame, old, new):
    return data_frame.na.replace(old, new)


@solid(
    inputs=[InputDefinition('sfo_weather_data', SparkDataFrameType)],
    outputs=[OutputDefinition(SparkDataFrameType)],
)
def process_sfo_weather_data(_context, sfo_weather_data):
    normalized_sfo_weather_data = replace_values_spark(sfo_weather_data, 'M', None)
    return rename_spark_dataframe_columns(normalized_sfo_weather_data, lambda c: c.lower())


@solid(
    name='load_data_to_database_from_spark',
    inputs=[
        InputDefinition(
            'data_frame',
            SparkDataFrameType,
            description='The pyspark DataFrame to load into the database.',
        )
    ],
    outputs=[OutputDefinition(SparkDataFrameType)],
    config_field=Field(Dict(fields={'table_name': Field(String, description='')})),
)
def load_data_to_database_from_spark(context, data_frame):
    context.resources.db_info.load_table(data_frame, context.solid_config['table_name'])
    # TODO Flow more information down to the client
    # We should be able to flow multiple key value pairs down to dagit
    # See https://github.com/dagster-io/dagster/issues/1408
    yield Materialization(
        path='Persisted Db Table: {table_name}'.format(
            table_name=context.solid_config['table_name']
        )
    )
    yield Result(data_frame)


@solid(
    name='subsample_spark_dataset',
    description='Subsample a spark dataset.',
    config_field=Field(
        Dict(fields={'subsample_pct': Field(Int, description='')})
        # description='The integer percentage of rows to sample from the input dataset.'
    ),
    inputs=[
        InputDefinition(
            'data_frame', SparkDataFrameType, description='The pyspark DataFrame to subsample.'
        )
    ],
    outputs=[
        OutputDefinition(
            SparkDataFrameType,
            # description='A pyspark DataFrame containing a subsample of the input rows.',
        )
    ],
)
def subsample_spark_dataset(context, data_frame):
    return data_frame.sample(
        withReplacement=False, fraction=context.solid_config['subsample_pct'] / 100.0
    )


q2_sfo_outbound_flights = sql_solid(
    'q2_sfo_outbound_flights',
    '''
    select * from q2_on_time_data
    where origin = 'SFO'
    ''',
    'table',
    table_name='q2_sfo_outbound_flights',
)

average_sfo_outbound_avg_delays_by_destination = sql_solid(
    'average_sfo_outbound_avg_delays_by_destination',
    '''
    select
        cast(cast(arrdelay as float) as integer) as arrival_delay,
        cast(cast(depdelay as float) as integer) as departure_delay,
        origin,
        dest as destination
    from q2_sfo_outbound_flights
    ''',
    'table',
    table_name='average_sfo_outbound_avg_delays_by_destination',
    inputs=[InputDefinition('q2_sfo_outbound_flights', dagster_type=SqlTableName)],
)

ticket_prices_with_average_delays = sql_solid(
    'tickets_with_destination',
    '''
    select
        tickets.*,
        coupons.dest,
        coupons.destairportid,
        coupons.destairportseqid, coupons.destcitymarketid,
        coupons.destcountry,
        coupons.deststatefips,
        coupons.deststate,
        coupons.deststatename,
        coupons.destwac
    from
        q2_ticket_data as tickets,
        q2_coupon_data as coupons
    where
        tickets.itinid = coupons.itinid;
    ''',
    'table',
    table_name='tickets_with_destination',
)

tickets_with_destination = sql_solid(
    'tickets_with_destination',
    '''
    select
        tickets.*,
        coupons.dest,
        coupons.destairportid,
        coupons.destairportseqid, coupons.destcitymarketid,
        coupons.destcountry,
        coupons.deststatefips,
        coupons.deststate,
        coupons.deststatename,
        coupons.destwac
    from
        q2_ticket_data as tickets,
        q2_coupon_data as coupons
    where
        tickets.itinid = coupons.itinid;
    ''',
    'table',
    table_name='tickets_with_destination',
)

delays_vs_fares = sql_solid(
    'delays_vs_fares',
    '''
    with avg_fares as (
        select
            tickets.origin,
            tickets.dest,
            avg(cast(tickets.itinfare as float)) as avg_fare,
            avg(cast(tickets.farepermile as float)) as avg_fare_per_mile
        from tickets_with_destination as tickets
        where origin = 'SFO'
        group by (tickets.origin, tickets.dest)
    )
    select
        avg_fares.*,
        avg(avg_delays.arrival_delay) as avg_arrival_delay,
        avg(avg_delays.departure_delay) as avg_departure_delay
    from
        avg_fares,
        average_sfo_outbound_avg_delays_by_destination as avg_delays
    where
        avg_fares.origin = avg_delays.origin and
        avg_fares.dest = avg_delays.destination
    group by (
        avg_fares.avg_fare,
        avg_fares.avg_fare_per_mile,
        avg_fares.origin,
        avg_delays.origin,
        avg_fares.dest,
        avg_delays.destination
    )
    ''',
    'table',
    table_name='delays_vs_fares',
    inputs=[
        InputDefinition('tickets_with_destination', SqlTableName),
        InputDefinition('average_sfo_outbound_avg_delays_by_destination', SqlTableName),
    ],
)

eastbound_delays = sql_solid(
    'eastbound_delays',
    '''
    select
        avg(cast(cast(arrdelay as float) as integer)) as avg_arrival_delay,
        avg(cast(cast(depdelay as float) as integer)) as avg_departure_delay,
        origin,
        dest as destination,
        count(1) as num_flights,
        avg(cast(dest_latitude as float)) as dest_latitude,
        avg(cast(dest_longitude as float)) as dest_longitude,
        avg(cast(origin_latitude as float)) as origin_latitude,
        avg(cast(origin_longitude as float)) as origin_longitude
    from q2_on_time_data
    where
        cast(origin_longitude as float) < cast(dest_longitude as float) and
        originstate != 'HI' and
        deststate != 'HI' and
        originstate != 'AK' and
        deststate != 'AK'
    group by (origin,destination)
    order by num_flights desc
    limit 100;
    ''',
    'table',
    table_name='eastbound_delays',
)

westbound_delays = sql_solid(
    'westbound_delays',
    '''
    select
        avg(cast(cast(arrdelay as float) as integer)) as avg_arrival_delay,
        avg(cast(cast(depdelay as float) as integer)) as avg_departure_delay,
        origin,
        dest as destination,
        count(1) as num_flights,
        avg(cast(dest_latitude as float)) as dest_latitude,
        avg(cast(dest_longitude as float)) as dest_longitude,
        avg(cast(origin_latitude as float)) as origin_latitude,
        avg(cast(origin_longitude as float)) as origin_longitude
    from q2_on_time_data
    where
        cast(origin_longitude as float) > cast(dest_longitude as float) and
        originstate != 'HI' and
        deststate != 'HI' and
        originstate != 'AK' and
        deststate != 'AK'
    group by (origin,destination)
    order by num_flights desc
    limit 100;
    ''',
    'table',
    table_name='westbound_delays',
)

delays_by_geography = notebook_solid(
    'delays_by_geography',
    'Delays_by_Geography.ipynb',
    inputs=[
        InputDefinition(
            'westbound_delays',
            SqlTableName,
            description='The SQL table containing westbound delays.',
        ),
        InputDefinition(
            'eastbound_delays',
            SqlTableName,
            description='The SQL table containing eastbound delays.',
        ),
    ],
    outputs=[
        OutputDefinition(
            dagster_type=FileFromPath,
            # name='plots_pdf_path',
            description='The saved PDF plots.',
        )
    ],
)

delays_vs_fares_nb = notebook_solid(
    'fares_vs_delays',
    'Fares_vs_Delays.ipynb',
    inputs=[
        InputDefinition(
            'table_name', SqlTableName, description='The SQL table to use for calcuations.'
        )
    ],
    outputs=[
        OutputDefinition(
            dagster_type=FileFromPath,
            # name='plots_pdf_path',
            description='The path to the saved PDF plots.',
        )
    ],
)

sfo_delays_by_destination = notebook_solid(
    'sfo_delays_by_destination',
    'SFO_Delays_by_Destination.ipynb',
    inputs=[
        InputDefinition(
            'table_name', SqlTableName, description='The SQL table to use for calcuations.'
        )
    ],
    outputs=[
        OutputDefinition(
            dagster_type=FileFromPath,
            # name='plots_pdf_path',
            description='The path to the saved PDF plots.',
        )
    ],
)


@solid(
    inputs=[
        InputDefinition('april_data', SparkDataFrameType),
        InputDefinition('may_data', SparkDataFrameType),
        InputDefinition('june_data', SparkDataFrameType),
        InputDefinition('master_cord_data', SparkDataFrameType),
    ],
    outputs=[OutputDefinition(SparkDataFrameType)],
    config_field=Field(
        Dict(fields={'subsample_pct': Field(Int, description='')})
        # description='The integer percentage of rows to sample from the input dataset.'
    ),
    description='''
    This solid takes April, May, and June data and coalesces it into a q2 data set.
    It then joins the that origin and destination airport with the data in the
    master_cord_data.
    ''',
)
def process_q2_data(context, april_data, may_data, june_data, master_cord_data):

    dfs = {'april': april_data, 'may': may_data, 'june': june_data}

    missing_things = []

    for required_column in ['DestAirportSeqID', 'OriginAirportSeqID']:
        for month, df in dfs.items():
            if required_column not in df.columns:
                missing_things.append({'month': month, 'missing_column': required_column})

    yield ExpectationResult(
        success=not bool(missing_things),
        name='airport_ids_present',
        message='Sequence IDs present in incoming monthly flight data.',
        result_metadata={'missing_columns': missing_things},
    )

    yield ExpectationResult(
        success=set(april_data.columns) == set(may_data.columns) == set(june_data.columns),
        name='flight_data_same_shape',
        result_metadata={'columns': april_data.columns},
    )

    q2_data = april_data.union(may_data).union(june_data)
    sampled_q2_data = q2_data.sample(
        withReplacement=False, fraction=context.solid_config['subsample_pct'] / 100.0
    )
    sampled_q2_data.createOrReplaceTempView('q2_data')

    dest_prefixed_master_cord_data = do_prefix_column_names(master_cord_data, 'DEST_')
    dest_prefixed_master_cord_data.createOrReplaceTempView('dest_cord_data')

    origin_prefixed_master_cord_data = do_prefix_column_names(master_cord_data, 'ORIGIN_')
    origin_prefixed_master_cord_data.createOrReplaceTempView('origin_cord_data')

    full_data = context.resources.spark.sql(
        '''
        SELECT * FROM origin_cord_data
        LEFT JOIN (
            SELECT * FROM q2_data
            LEFT JOIN dest_cord_data ON
            q2_data.DestAirportSeqID = dest_cord_data.DEST_AIRPORT_SEQ_ID
        ) q2_dest_data 
        ON origin_cord_data.ORIGIN_AIRPORT_SEQ_ID = q2_dest_data.OriginAirportSeqID
        '''
    )

    yield Result(rename_spark_dataframe_columns(full_data, lambda c: c.lower()))
