from .utils import execute_dagster_graphql


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
