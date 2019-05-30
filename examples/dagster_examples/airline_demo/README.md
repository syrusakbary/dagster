# Airline demo

This repository is intended as a fleshed-out demo of Dagster's capabilities. It defines three
realistic data pipelines corresponding to stereotyped download, ingest, and analysis phases of
typical data science workflows, using real-world airline data. Although the view of the pipelines
provided by the Dagster tooling is unified, in typical practice we expect that each pipeline is
likely to be the responsibility of individuals with more or less clearly distinguished roles.

Use the airline demo to familiarize yourself with the features of the Dagster tooling in a more
fleshed-out context than the introductory tutorial, and as a reference when building your own
first production pipelines in the system. Comments and suggestions are enthusiastically encouraged!

## Getting started

To run the airline demo pipelines locally, you'll need

- An Internet connection
- AWS credentials in the ordinary [boto3 credential chain](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html)
- An [Apache Spark](https://spark.apache.org/downloads.html) install
- A running Postgres database available at `postgresql://test:test@127.0.0.1:5432/test`. (A
  docker-compose file is provided in this repo; run `docker-compose up` from the root of the
  airline demo.)

Use pip to install the demo's Python requirements:

    pip install -e .

Then just run dagit from the root of the repo:

    dagit

## Pipelines and config

The demo defines a single repository with two pipelines, in `airline_demo/pipelines.py`:

- **airline_demo_ingest_pipeline** grabs data archives from S3 and unzips them, reads the raw data
  into Spark, performs some typical manipulations on the data, and then loads tables into a data warehouse.
- **airline_demo_warehouse_pipeline** performs typical in-warehouse analysis and manipulations
  using SQL, and then generates and archives analysis artifacts and plots using Jupyter notebooks.

Sample configuration files for running the demo pipelines are provided under `environments/`. To run
the pipelines locally, use the configuration files that begin with the prefix `local_`.

To avoid unnecessary duplication, the config that is common to all of the pipelines is factored
out into `local_base.yaml` file. Recall that when running a pipeline using `dagster pipeline execute`
you can pass more than one yaml file using the `-e` flag, and these will be combined.

## Running tests

You won't want to suppress test output if you want to see loglines from dagster:

    pytest -s

We use [pytest marks](https://docs.pytest.org/en/latest/example/markers.html#mark-examples) to
identify useful subsets of tests. You can find the marks we use in `airline_demo_tests/marks.py`.
For instance, to run only those tests that do not require Spark, you can run:

    pytest -m "not spark"

## The ingest pipeline

<!-- FIXME -->
<!-- ![Download pipeline](img/ingest_pipeline.png) -->

The `airline_demo_ingest_pipeline` models the first stage of most project-oriented data science
workflows, in which raw data is consumed from a variety of sources.

For demo purposes, we've put our source files in a publicly-readable S3 repository. In practice,
these might be files in S3 or other cloud storage systems; publicly available datasets downloaded
over http; or batch files in an SFTP drop.

### Running the pipeline locally with test config

If you want to start by running this pipeline, try the config fragment in
`environments/local_fast_ingest.yaml`. The first time you run this pipeline, you'll likely see a
bunch of log lines in the terminal running dagit as Spark dependencies are resolved.

This config fragment points to cut-down versions of the original data files on S3. It can be good
practice to maintain similar test sets so that you can run fast versions of your data pipelines
locally or in test environments. While there are many faults that will not be caught by using small
cut-down or synthetic data sets -- for example, data issues that may only appear in production data
or at scale -- this practice will allow you to verify the integrity of your pipeline construction
and to catch at least some semantic issues.

<!-- FIXME -->
<!-- ![Download pipeline run](img/ingest_pipeline_run.png) -->

### Defining a pipeline with reusable solids

Let's start by looking at the pipeline definition (in `airline_demo/pipelines.py`). where you'll see
that we rely heavily on `SolidInstance` to build our pipeline, for example:

    SolidInstance('unzip_file', alias='unzip_may_on_time_data'): {
        'archive_path': DependencyDefinition('download_may_on_time_data')
    }

This API lets us define aliased instances (`unzip_may_on_time_data`) of reusable library solids
(`unzip_file`).

In general, you won't want every data science user in your organization to have to roll their own
implementation of common functionality like downloading and unzipping files. Instead, you'll want to
abstract common functionality into reusable solids, separating task-specific parameters out into
declarative config, and building up a library of building blocks for new data pipelines.

### Strongly typed config and outputs

The config for each of our solids specifies everything it needs in order to interact with the
external environment. In YAML, an entry in the config for one of our solids aliasing
`download_from_s3` looks like this:

download_master_cord_data:
config:
bucket: dagster-airline-demo-source-data
key: 954834304_T_MASTER_CORD.zip
skip_if_present: true
target_path: source_data/954834304_T_MASTER_CORD.zip

Because each of these values is strongly typed, we'll get rich error information in the dagit
config editor (or when running pipelines from the command line) when a config value is incorrectly
specified.

<!-- FIXME -->
<!-- ![Download pipeline bad config](img/download_pipeline_bad_config.png) -->

While this may seem like a mere convenience, in production contexts it can dramatically reduce
avoidable errors. Consider boto3's [S3.Client.put_object](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_object)
method, which has 28 parameters, many restricted in obscure ways (for example,
`ServerSideEncryption` must be one of `'AES256'|'aws:kms'`). Strongly typed config schemas can catch
any error of this type.

By setting the `description` on each of our config members, we also get easily navigable
documentation in dagit. Users of library solids no longer need to investigate implementations in
order to understand what values are required, or what they do -- enabling more confident reuse.

<!-- FIXME -->
<!-- ![Download pipeline config docs](img/download_pipeline_config_docs.png) -->

<!-- FIXME -->
<!-- ### Custom types

Note that the output of this solid is also a List -- in this case, a `List(FileExistsAtPath)`. We've
defined a custom output type to illustrate the richness of the Dagster type system:

    from dagster.core.types.runtime import Stringish
    from dagster.utils import safe_isfile

    class FileExistsAtPath(Stringish):
        def __init__(self):
            super(FileExistsAtPath, self).__init__(description='A path at which a file actually exists')

        def coerce_runtime_value(self, value):
            value = super(FileExistsAtPath, self).coerce_runtime_value(value)
            return self.throw_if_false(safe_isfile, value)

By overriding `coerce_runtime_value` to check if a file actually exists at the specified path, we
can lever the type system to make runtime guarantees about the integrity of our pipeline. -->

### Robust solids for development workflows

Notice the `skip_if_present` key in the config for both `download_from_s3` and `unzip_file`. We've
included this to illustrate how you can introduce knobs into your solids that make moving between
development, test, and production environments and workflows easier.

In production, you may have pipelines that grab large files from batch processes or filedrops, and
that may take minutes or hours to execute. But in development, you probably won't want to download
large data every time you make a small tweak to a pipeline. Practitioners often find themselves
writing special-case wrappers to handle their local workflows -- for instance, to download files
only if they are not already present on the local file system.

Here, we've moved that logic into the body of the solid itself. Because we can turn this feature on
and off with config, we don't need to write ad hoc tooling to support local workflows. Instead, the
same pipeline can run locally as runs in production. This makes it easier both to develop locally
with a short feedback cycle and to write and run tests against pipeline code.

### Running on production data

Don't worry, we've got plenty of big(gish) data to run through this pipeline. Instead of the
`local_fast_ingest.yaml` config fragment, use `local_full_ingest.yaml` -- but be prepared to wait!
In practice, you can use this pattern to run your Dagster pipelines against synthetic, anonymized,
or subsampled datasets in test and development environments.

<!-- FIXME -->
<!-- ### Context definitions: using configurable resources to interact with the external world

In practice, you'll want to run your pipelines in environments that vary widely in their available
facilities. For example, when running an ingestion pipeline locally for test or development, you
may want to use a local Spark cluster; but when running in production, you will probably want to
target something heftier, like an ephemeral EMR cluster or your organization's on-prem Spark
cluster. Or, you may want to target a locally-running Postgres as your "data warehouse" in local
test/dev, but target a Redshift cluster in production and production tests. Ideally, we want this
to be a matter of flipping a config switch.

Let's look at how we make configurable resources available to our pipelines. In
`airline_demo/pipelines.py`, you'll find that we define multiple contexts within which our pipelines
may run:

    CONTEXT_DEFINITIONS = {'test': test_context, 'local': local_context, 'prod': prod_context}

This is intended to mimic a typical setup where you may have pipelines running locally on developer
machines, often with a (anonymized or scrubbed) subset of data and with limited compute resources;
remotely in CI/CD, with access to a production or replica environment, but where speed is of the
essence; and remotely in production on live data.

    local_context = PipelineContextDefinition(
        resources={
            'db_info': define_postgres_db_info_resource(),
            ...
        },
    )

    prod_context = PipelineContextDefinition(
        resources={
            'db_info': define_redshift_db_info_resource(),
            ...
        },
    )

Here we've defined a `db_info` resource that exposes a unified API to our solid logic, but that
wraps two very different underlying assets -- in one case, a Postgres database, and in the other,
a Redshift cluster. Let's look more closely at how this is implemented for the Postgres case.

First, we define the `db_info` resource itself:

    from collections import namedtuple

    DbInfo = namedtuple('DbInfo', 'engine url jdbc_url dialect load_table')

This resource exposes a SQLAlchemy engine, the URL of the database (in two forms), metadata about
the SQL dialect that the database speaks, and a utility function, `load_table`, which loads a
Spark data frame into the target database. In practice, we would probably find that over time we
wanted to add or subtract from this interface, rework its implementations, or factor it into
multiple resources. Because the type definition, config definitions, and implementations are
centralized -- rather than spread out across the internals of many solids -- this is a relatively
easy task.

Next, we define the config required to instantiate our resource:

    from dagster import Dict

    PostgresConfigData = Dict(
        {
            'postgres_username': Field(String),
            'postgres_password': Field(String),
            'postgres_hostname': Field(String),
            'postgres_db_name': Field(String),
        }
    )

Obviously, this config will differ for Redshift, as it might if we had to reach our database through
a proxy server, or using a different authentication schema.

Finally, we bring it all together in the `define_postgres_db_info_resource` function:

    from dagster import ResourceDefinition, Field

    def define_postgres_db_info_resource():
        def _create_postgres_db_info(init_context):
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

        return ResourceDefinition(
            resource_fn=_create_postgres_db_info, config_field=Field(PostgresConfigData)
        )

Note that by setting the strongly typed `config_field` parameter, we now have typeahead
support in dagit and rich error messages for the configuration of our external resources. This can
be extremely valuable in the case of notoriously complex configuration formats, such as Spark's. -->

<!-- FIXME -->
<!-- ![Ingest pipeline resource config](img/ingest_pipeline_resource_config.png) -->

### Ingesting data to Spark data frames

The ingestion pipeline contains a number of aliases of the `ingest_csv_to_spark` solid,
independently configured with their inputs, e.g.:

    ingest_april_on_time_data:
    inputs:
        input_csv: source_data/On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2018_4.csv

Note the type signature of these solids.

![Ingest pipeline type signature](img/ingest_pipeline_type_signature.png)

The output has type `SparkDataFrameType`, a custom Dagster type that wraps a pyspark.sql.DataFrame.
Defining types of this kind is straightforward and provides additional safety when your solids pass
Python objects to each other:

    from dagster import as_dagster_type
    from pyspark.sql import DataFrame

    SparkDataFrameType = as_dagster_type(
        DataFrame, name='SparkDataFrameType', description='A Pyspark data frame.'
    )

The transformation solids that follow all use the SparkDataFrameType for their intermediate results.
You might also build DAGs where Pandas data frames, or some other in-memory Python object, are the
common intermediate representation.

<!-- FIXME -->
<!-- ### Implicit dependencies between pipelines

We configured the ingestion pipeline by specifying paths to source .csv files for each root node of
the DAG. But we know that in order for these files to be where we expect them, the download pipeline
must first have run. We have an implicit dependency between pipelines that isn't expressed in code.

In practice, you'll need to decide where to draw the line between pipelines, just as you'll need to
decide which units of computation are best suited to be expressed as solids. In this demo, we
hypothesize that pipelines correspond well to conceptually independent workflows that are likely to
be run and maintained by distinct teams.

A typical ingestion pipeline might be maintained by an ops, software engineering, or data
engineering team. It's likely to have to consider a lot of messy infastructural details, like
external secrets, connection configuration, protocols, retry logic, and encodings.

A typical ingestion pipeline might be maintained by data engineers and ETL engineers. It will make
use of common internal infrastructure and require data to be munged into the standard
representations exposed to analysts and data scientists in the data warehouse.

Typical data warehouse pipelines will involve a heterogeneous mix of work in Jupyter notebooks
(in Python, R, Scala, etc.) and SQL, and might have outputs to reporting, real time messaging, or
shared file servers. They will typically be maintained by dedicated analysts and data scientists.

In an organization that adopts Dagster, software and data engineering teams will tend to build
library solids and resources for internal clients, focusing on making their existing systems
available to pipeline authors. They will also likely be responsible for deploying and orchestrating
pipelines in production. Analysts and data scientists will tend to write pipelines that connect
library solid, as well as logic in familiar tools (like SQL and Jupyter) that can be easily wrapped
by utility solids. -->

### Abstract building blocks for specific transformations

The bulk of this pipeline is built out of generic library solids, which are presented as examples
of the kind of reusable abstract building blocks you'll be able to write to simplify the expression
of common workloads:

- **subsample_spark_dataset** (4x) randomly subsamples a dataset using `data_frame.sample`.
  Abstracting this out makes it clear which datasets may be subsampled and which may not be (e.g.,
  lookup tables like the `master_cord_data`) in this pipeline). Because subsampling is now
  controlled by config, it's easy to turn off in production (by sampling 100% of the rows) or to
  adjust progressively in test. In practice, you might want to extend this solid, e.g., by allowing
  the random seed to be set via config to ensure deterministic test output.
- **prefix_column_names** (2x) wraps a use of `data_frame.toDF` to rename the columns of a data
  frame, adding a prefix to avoid collisions and for clarity when columns with the same name are
  joined from two separate source data frames.
- **join_spark_data_frames** (2x) wraps `data_frame.join`, allowing users to set the join parameters
  in config. You can use abstractions like this and strongly typed config to guard against common
  errors: for example, by specifying a `joinType` config value as an `Enum`, you could enforce
  Spark's restriction on join types _at config time_.

Throughout, we work with Spark data frames, but it's straightforward to write similar solids that
manipulate .csv files, parquet files, Pandas data frames, and other common data formats.

Each of your pipelines will also have idiosyncratic operations that don't necessarily abstract
well. Here, for instance, our weather data uses the value `M` to specify a missing value. The
`normalize_weather_na_values` solid handles this operation for us, cleanly separating the weather
data-specific cleanup operations from the rest of our logic. (Of course, in practice, you may want
to write a more generic `normalize_na_values` solid that allows the user to specify the source
data's missing value representation[s] in config.)

### Loading data to the warehouse

The terminal nodes of this pipeline are all aliased instances of `load_data_to_database_from_spark`,
which abstracts the operation of loading a Spark data frame to a database -- either our production
Redshift cluster or our local Postgres in test:

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
        return data_frame

Note how using the `db_info` resource simplifies this operation. There's no need to pollute the
implementation of our DAGs with specifics about how to connect to outside databases, credentials,
formatting details, retry or batching logic, etc. This greatly reduces the opportunities for
implementations of these core external operations to drift and introduce subtle bugs, and cleanly
separates infrastructural concerns from the logic of any particular data processing pipeline.

## The warehouse pipeline

![Warehouse pipeline](img/warehouse_pipeline.png)

The `airline_demo_warehouse_pipeline` models the analytics stage of a typical data science workflow.
This is a heterogeneous-by-design process in which analysts, data scientists, and ML engineers
incrementally derive and formalize insights and analytic products (charts, data frames, models, and
metrics) using a wide range of tools -- from SQL run directly against the warehouse to Jupyter
notebooks in Python, R, or Scala.

### The sql_solid: wrapping foreign code in a solid

How do we actually package the SQL for execution and display with Dagster and Dagit? Let's look at
the implementation of the `sql_solid`:

    class SqlTableName(Stringish):
        def __init__(self):
            super(SqlTableName, self).__init__(description='The name of a database table')

We introduce the custom type `SqlTableName` to make it as clear as possible what we're expecting
to return from a solid that executes a SQL statement, and what we're expecting to consume
downstream.

Next we define `sql_solid` itself. This function wraps a SQL `select` statement in a transform
function that executes the statement (again, using the database engine exposed by the `db_info`
resource) against the database, materializing the result as a table, and returning the name of the
newly created table.

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

        materialization_strategy_output_types = {
            'table': SqlTableName,
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

        sql_statement = (
            'drop table if exists {table_name};\n' 'create table {table_name} as {select_statement};'
        ).format(table_name=table_name, select_statement=select_statement)

        def transform_fn(context, _inputs):
            '''Inner function defining the new solid.

            Args:
                info (ExpectationExecutionInfo): Must expose a `db` resource with an `execute` method,
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
            transform_fn=transform_fn,
            description=description,
            metadata={'kind': 'sql', 'sql': sql_statement},
        )

There are a couple of things to note about this implementation. First of all, we make sure to
set the `metadata` key on our generated solid so that Dagit knows how to display the SQL that it
will execute (just double-click on any solid tagged with a small red `sql`):

![Warehouse pipeline SQL](img/warehouse_pipeline_sql_display.png)

Second, note that even though this wrapper only implements materialization of a SQL statement as a
table, we've made `materialization_strategy` configurable. This lets data engineers add new
capabilities for frontend analysts without having to rewrite any SQL. For example, we might add a
materialization strategy which created a materialized view instead of a table; an in-memory
SQLAlchemy query which could be executed or transformed by downstream solids; a SQLAlchemy
ResultProxy representing the records resulting from executing the query; or a materialization of
the results as a Pandas data frame, Spark data frame, parquet file, etc. The point is to decouple
the implementation of these strategies from the logic of the query itself.

Suppose that we wanted to change the logic of `sql_statement` from
`drop_table_if_exists; create table` to something more sophisticated (perhaps a conditional upsert,
or adding a new partition to an existing partitioned table). Again, rather than relying on analysts
to write or maintain many separate copies of the boilerplate around the select statement, we can
make the change once and expose the new functionality everywhere we execute SQL in our pipelines.

Third, note how straightforward the interface to `sql_statement` is. To define a new solid executing
a relatively complex computation against the data warehouse, an analyst need only write the following
code:

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

This kind of interface can supercharge the work of analysts who are highly skilled in SQL, but
for whom fully general-purpose programming in Python may be uncomfortable. Analysts need only master
a very constrained interface in order to define their SQL statements' data dependencies and outputs
in a way that allows them to be orchestrated and explored in heterogeneous DAGs containing other
forms of computation, and must make only minimal changes to code (in some cases, no changes) in
order to take advantage of centralized infrastructure work.

Finally, observe the opportunities for extensibility in the construction of the SQL statement
itself. In this implementation, by convention we require the analyst to be responsible for
explicitly defining inputs of types `SqlTableName` and linking those to the output of previous
SQL solids -- but we don't actually consume these inputs in any way other than to order the DAG's
dependencies.

    sql_statement = (
        'drop table if exists {table_name};\n' 'create table {table_name} as {select_statement};'
    ).format(table_name=table_name, select_statement=select_statement)

We could also change our implementation of the SQL statement construction, moving beyond string
formatting to use fuller-featured tools like SQLAlchemy or Jinja templating to dynamically
construct SQL statements based on the values of inputs to the solid.

But don't overcomplicate matters! A simple wrapper like the one we've presented here might be
able to get your organization 80% or more of the way there.

### Dagstermill: executing and checkpointing notebooks

Notebooks are a flexible way and increasingly ubiquitous way to explore datasets and build data
products -- from transformed or augmented datasets to charts and metrics to deployable machine
learning models. But their very flexibility -- the way they allow analysts to move seamlessly from
interactive exploration of data to scratch code and finally to actionable results -- can make them
difficult to productionize.

Our approach, built on the [papermill](https://github.com/nteract/papermill) library, embraces
the diversity of code in notebooks. Rather than requiring notebooks to be rewritten or "cleaned up"
in order to consume inputs from other nodes in a pipeline or to produce outputs for downstream
nodes, we can just add a few cells to provide a thin wrapper around an existing notebook.

Notebook solids can be identified by the small red `ipynb` tag in Dagit. As with SQL solids, they
can be explored from within Dagit by drilling down on the tag:

![Warehouse pipeline notebook](img/warehouse_pipeline_notebook_display.png)

Let's start with the definition of our `notebook_solid` helper:

    import os

    from dagstermill import define_dagstermill_solid

    def _notebook_path(name):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notebooks', name)


    def notebook_solid(name, notebook_path, inputs, outputs):
        return define_dagstermill_solid(name, _notebook_path(notebook_path), inputs, outputs)

This is just a wrapper around Dagstermill's `define_dagstermill_solid` which tells Dagstermill
where to look for the notebooks. We define a new solid as follows:

    sfo_delays_by_destination = notebook_solid(
        'sfo_delays_by_destination',
        'SFO Delays by Destination.ipynb',
        inputs=[
            InputDefinition(
                'db_url', String, description='The db_url to use to construct a SQLAlchemy engine.'
            ),
            InputDefinition(
                'table_name', SqlTableName, description='The SQL table to use for calcuations.'
            ),
        ],
        outputs=[
            OutputDefinition(
                dagster_type=Path,
                # name='plots_pdf_path',
                description='The path to the saved PDF plots.',
            )
        ],
    )

As always, we define the inputs and outputs of the new solid. Within the notebook itself, we only
need to add a few lines of boilerplate. Dagstermill exposes a command line facility to scaffold a
notebook for you, so that you don't need to manage this boilerplate directly. Just run, e.g.:

    dagstermill create-notebook -n define_repo -m airline_demo.repository -note Delays_by_Geography

The arguments to `-m` and `-n` tell dagstermill where to find the repository that the new notebook
solid will belong to, and the argument to `-note` tells dagstermill what to call the new notebook.

You can also manually insert the boilerplate. In either case, at the top of the notebook, we
declare the notebook to be a solid and register it to our repository with the following code:

    import dagstermill as dm
    from dagster_examples.airline_demo.repository import define_repo
    dm.register_repository(define_repo())

In your own pipelines, you'll register your solid to your own repositories.

The call to `dagstermill.register_repository` identifies the notebook contents with the notebook
solid we defined in our pipeline.

Then, in a cell with the `parameters` tag, we write:

    context = dm.get_context()
    db_url = 'postgresql://test:test@127.0.0.1:5432/test'
    eastbound_delays = 'eastbound_delays'
    westbound_delays = 'westbound_delays'

When dagstermill executes this notebook as part of a pipeline, values for these inputs will be
injected from the output of upstream solids.

Finally, at the very end of the notebook, we yield the result back to the pipeline:

    dm.yield_result(pdf_path, 'result')

<!-- TODOs (with db resource)
    - Discuss output notebooks
    - Discuss dagstermill resources/context
-->

<!--
FIXME need to actually describe how to run this pipeline against AWS

### Orchestrating AWS resources
The pipelines defined in this repository can run against a local Spark cluster
and Postgres instance, or they can run against a Redshift cluster and Spark
running on Amazon EMR.

We manage AWS resources with [pulumi](https://github.com/pulumi/pulumi).
First, install the pulumi CLI:

    brew install pulumi

Pulumi resources are divided by "project". To spin resources up for a demo run,
use the `demo_resources` project.

First, make sure you have the requirements. (You'll need to have already
installed TypeScript.)

    cd pulumi/demo_resources
    npm install

Then, you can bring up resources by running:

    pulumi up

This will take between 4 and 5 minutes.

To destroy resources, run:

    pulumi destroy

<small>
*Warning*: Currently we are unable to cleanly tear down the VPC using pulumi
because of dependency errors like the following:

    error: Plan apply failed: deleting urn:pulumi:demo_resources-dev::demo_resources::aws-infra:network:Network$aws:ec2/vpc:Vpc::airline_demo_vpc: DependencyViolation: The vpc 'vpc-01a7f7c286196cdc0' has dependencies and cannot be deleted.
        status code: 400, request id: 03a586f3-e17e-41e2-b5fd-c4275226df30

It's unclear whether this is an issue with pulumi/aws-infra or something else,
maybe the autogenerated EMR slave and master security groups (? -- but if so,
see https://github.com/pulumi/pulumi/issues/1691 -- or, if this is in fact an issue
with the underlying terraform provider, see https://github.com/terraform-providers/terraform-provider-aws/issues/3465,
and many other issues suggesting the EMR resource in the AWS provider is not
fully mature). There is no good way to find out *which* dependency is causing
this error (generated in the AWS CLI), and no way to force delete dependencies
from the command line (See: https://github.com/aws/aws-cli/issues/1721,
https://forums.aws.amazon.com/thread.jspa?threadID=223412).

Right now the workaround is to wait for a timeout (about 15 minutes), then
manually delete the VPC from the console, which will force-delete dependencies.
</small>

### Issues with general availability
- Right now the pulumi spec, as well as the sample config, expect that you will
be able to orchestrate a Redshift cluster at `db.dagster.io` and an EMR cluster
at `spark.dagster.io`. If you are running this demo and you do not control
`dagster.io`, you will need to edit both the pulumi project and the config to
point these at DNS you do control.

-->

<!-- ### TODOs

- Flesh out unit tests for solids
- Write ephemeral EMR cluster resource
- Add expectations
- Maybe implement templated SQL handling
- Add sub-DAG tests -->
