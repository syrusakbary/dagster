'''
Repository of test pipelines
'''

from dagster import (
    Dict,
    Field,
    Int,
    ModeDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    resource,
    solid,
)


def define_empty_pipeline():
    return PipelineDefinition(name='empty_pipeline', solids=[])


def define_single_mode_pipeline():
    @solid
    def return_two(_context):
        return 2

    return PipelineDefinition(
        name='single_mode', solids=[return_two], mode_definitions=[ModeDefinition(name='the_mode')]
    )


def define_multi_mode_pipeline():
    @solid
    def return_three(_context):
        return 3

    return PipelineDefinition(
        name='multi_mode',
        solids=[return_three],
        mode_definitions=[ModeDefinition(name='mode_one'), ModeDefinition('mode_two')],
    )


def define_multi_mode_with_resources_pipeline():
    @resource(config_field=Field(Int))
    def adder_resource(init_context):
        return lambda x: x + init_context.resource_config

    @resource(config_field=Field(Int))
    def multer_resource(init_context):
        return lambda x: x * init_context.resource_config

    @resource(config_field=Field(Dict({'num_one': Field(Int), 'num_two': Field(Int)})))
    def double_adder_resource(init_context):
        return (
            lambda x: x
            + init_context.resource_config['num_one']
            + init_context.resource_config['num_two']
        )

    @solid(resources={'op'})
    def apply_to_three(context):
        return context.resources.op(3)

    return PipelineDefinition(
        name='multi_mode_with_resources',
        solids=[apply_to_three],
        mode_definitions=[
            ModeDefinition(name='add_mode', resources={'op': adder_resource}),
            ModeDefinition(name='mult_mode', resources={'op': multer_resource}),
            ModeDefinition(
                name='double_adder_mode',
                resources={'op': double_adder_resource},
                description='Mode that adds two numbers to thing',
            ),
        ],
    )


def define_repository():
    return RepositoryDefinition.eager_construction(
        name='dagster_test_repository',
        pipelines=[
            define_empty_pipeline(),
            define_single_mode_pipeline(),
            define_multi_mode_pipeline(),
            define_multi_mode_with_resources_pipeline(),
        ],
    )


def test_repository_construction():
    assert define_repository()
