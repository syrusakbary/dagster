from .setup import execute_dagster_graphql, define_context

ENVIRONMENT_SCHEMA_QUERY = '''
query($selector: ExecutionSelector! $mode: String!)
{
  environmentSchemaOrError(selector: $selector, mode: $mode){
    __typename
    ... on EnvironmentSchema {
      environmentType {
        key
      }
    }
  }
}
'''


def test_successful_enviroment_schema():
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_QUERY,
        variables={'selector': {'name': 'multi_mode_with_resources'}, 'mode': 'add_mode'},
    )
    assert result.data['environmentSchemaOrError']['__typename'] == 'EnvironmentSchema'


def test_environment_schema_pipeline_not_found():
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_QUERY,
        variables={'selector': {'name': 'jkdjfkdjfd'}, 'mode': 'add_mode'},
    )
    assert result.data['environmentSchemaOrError']['__typename'] == 'PipelineNotFoundError'


def test_environment_schema_solid_not_found():
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_QUERY,
        variables={
            'selector': {'name': 'multi_mode_with_resources', 'solidSubset': ['kdjfkdj']},
            'mode': 'add_mode',
        },
    )
    assert result.data['environmentSchemaOrError']['__typename'] == 'SolidNotFoundError'


def test_environment_schema_mode_not_found():
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_QUERY,
        variables={'selector': {'name': 'multi_mode_with_resources'}, 'mode': 'kdjfdk'},
    )
    assert result.data['environmentSchemaOrError']['__typename'] == 'ModeNotFoundError'
