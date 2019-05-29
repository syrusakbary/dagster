from .setup import execute_dagster_graphql, define_context, define_examples_context


def execute_preset_query(pipeline_name, context):
    pipeline_query = '''
        query PresetsQuery($name: String!) {
            pipeline(params: { name: $name }) {
                name
                presets {
                    __typename
                    name
                    solidSubset
                    environmentConfigYaml
                    mode
                }
            }
        }
    '''

    return execute_dagster_graphql(context, pipeline_query, variables={'name': pipeline_name})


def test_basic_preset_query_no_presets():
    result = execute_preset_query('csv_hello_world_two', define_context())
    assert result.data == {'pipeline': {'name': 'csv_hello_world_two', 'presets': []}}


def test_basic_preset_query_with_presets(snapshot):
    result = execute_preset_query('csv_hello_world', define_context())

    assert [preset_data['name'] for preset_data in result.data['pipeline']['presets']] == [
        'prod',
        'test',
    ]

    snapshot.assert_match(result.data)


def test_presets_on_examples(snapshot):
    context = define_examples_context()
    for pipeline_name in context.repository_definition.pipeline_names:
        snapshot.assert_match(execute_preset_query(pipeline_name, context).data)
