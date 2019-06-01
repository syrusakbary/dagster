from dagster import (
    Field,
    Int,
    DependencyDefinition,
    SolidInstance,
    InputDefinition,
    PipelineDefinition,
    execute_pipeline,
    solid as solid_dec,
    lambda_solid,
)

from dagster.core.definitions.pipeline import pipeline


from dagster.core.definitions.graph import (
    from_dep_func,
    DepGraphBuilder,
    DepGraphValue,
    DepSolidNode,
    DepSolidDefNode,
    construct_dep_dict,
)


def builder(graph):
    return graph.add_one(graph.return_one())


@lambda_solid
def return_one():
    return 1


@lambda_solid(inputs=[InputDefinition('num')])
def add_one(num):
    return num + 1


def test_basic_use_case():
    pipeline_def = PipelineDefinition(
        name='basic',
        solids=[return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )

    assert execute_pipeline(pipeline_def).result_for_solid('add_one').transformed_value() == 2


def graph_pipeline(solids, graph_fn):
    return PipelineDefinition(solids=solids, dependencies=from_dep_func(solids, graph_fn))


def test_basic_use_case_with_dsl():
    pipeline_def = graph_pipeline(
        [return_one, add_one], lambda graph: graph.add_one(num=graph.return_one())
    )

    assert execute_pipeline(pipeline_def).result_for_solid('add_one').transformed_value() == 2


def test_two_inputs_without_dsl():
    @lambda_solid(inputs=[InputDefinition('num_one'), InputDefinition('num_two')])
    def add(num_one, num_two):
        return num_one + num_two

    @lambda_solid
    def return_two():
        return 2

    @lambda_solid
    def return_three():
        return 3

    pipeline_def = PipelineDefinition(
        solids=[add, return_two, return_three],
        dependencies={
            'add': {
                'num_one': DependencyDefinition('return_two'),
                'num_two': DependencyDefinition('return_three'),
            }
        },
    )

    assert execute_pipeline(pipeline_def).result_for_solid('add').transformed_value() == 5


def test_two_inputs_with_dsl():
    @lambda_solid(inputs=[InputDefinition('num_one'), InputDefinition('num_two')])
    def add(num_one, num_two):
        return num_one + num_two

    @lambda_solid
    def return_two():
        return 2

    @lambda_solid
    def return_three():
        return 3

    pipeline_def = graph_pipeline(
        [add, return_two, return_three],
        lambda graph: graph.add(num_one=graph.return_two(), num_two=graph.return_three()),
    )

    assert execute_pipeline(pipeline_def).result_for_solid('add').transformed_value() == 5


def test_two_inputs_with_decorator():
    @lambda_solid(inputs=[InputDefinition('num_one'), InputDefinition('num_two')])
    def add(num_one, num_two):
        return num_one + num_two

    @lambda_solid
    def return_two():
        return 2

    @lambda_solid
    def return_three():
        return 3

    @pipeline(solids=[add, return_two, return_three])
    def decorator_test_pipeline(graph):
        return graph.add(num_one=graph.return_two(), num_two=graph.return_three())

    assert (
        execute_pipeline(decorator_test_pipeline).result_for_solid('add').transformed_value() == 5
    )


def test_basic_aliasing_with_dsl():
    pipeline_def = graph_pipeline(
        [return_one, add_one], lambda graph: graph.add_one.renamed(num=graph.return_one())
    )

    assert execute_pipeline(pipeline_def).result_for_solid('renamed').transformed_value() == 2


def test_basic_explicit_aliasing_with_dsl():
    pipeline_def = graph_pipeline(
        [return_one, add_one], lambda graph: graph.add_one.alias('renamed')(num=graph.return_one())
    )

    assert execute_pipeline(pipeline_def).result_for_solid('renamed').transformed_value() == 2


def test_complicated_graph():
    @solid_dec(config_field=Field(Int))
    def download_num(context):
        return context.solid_config

    @lambda_solid(inputs=[InputDefinition('num')])
    def unzip_num(num):
        return num

    @lambda_solid(inputs=[InputDefinition('num')])
    def ingest_num(num):
        return num

    @lambda_solid(inputs=[InputDefinition('num')])
    def subsample_num(num):
        return num

    @lambda_solid(inputs=[InputDefinition('num')])
    def canonicalize_num(num):
        return num

    @lambda_solid(inputs=[InputDefinition('num')])
    def load_num(num):
        return num + 3

    def graph_fn(graph):
        unzipped = graph.unzip_num.unzip_q2_coupon_data(
            num=graph.download_num.download_q2_coupon_data()
        )
        return graph.load_num.load_q2_coupon_data(
            num=graph.canonicalize_num.canonicalize_q2_coupon_data(
                num=graph.subsample_num.subsample_q2_coupon_data(
                    num=graph.ingest_num.ingest_q2_coupon_data(num=unzipped)
                )
            )
        )

    pipeline_def = graph_pipeline(
        solids=[download_num, unzip_num, ingest_num, subsample_num, canonicalize_num, load_num],
        graph_fn=graph_fn,
    )

    result = execute_pipeline(
        pipeline_def, {'solids': {'download_q2_coupon_data': {'config': 123}}}
    )

    assert result.result_for_solid('canonicalize_q2_coupon_data').transformed_value() == 123
    assert result.result_for_solid('load_q2_coupon_data').transformed_value() == 126


def test_dep_graph_basics():
    graph = DepGraphBuilder(solid_defs=[return_one, add_one])
    assert isinstance(graph.return_one, DepSolidDefNode)
    assert isinstance(graph.return_one(), DepGraphValue)
    assert isinstance(graph.return_one.renamed, DepSolidNode)
    assert isinstance(graph.return_one.renamed(), DepGraphValue)


def test_dep_full_graph_construction():
    graph = DepGraphBuilder(solid_defs=[return_one, add_one])

    return_one_output = graph.return_one()

    graph.add_one(num=return_one_output)

    assert construct_dep_dict(graph) == {
        SolidInstance('return_one', 'return_one'): {},
        SolidInstance('add_one', 'add_one'): {'num': DependencyDefinition('return_one')},
    }
