import copy
from dagster_graphql.test.utils import execute_dagster_graphql
from .utils import sync_execute_get_run_log_data, define_context

RUNS_QUERY = '''
query PipelineRunsRootQuery($name: String!) {
  pipeline(params: { name: $name }) {
    name
    runs {
      ...RunHistoryRunFragment
    }
  }
}

fragment RunHistoryRunFragment on PipelineRun {
  runId
  status
  pipeline {
    name
  }
  logs {
    nodes {
      __typename
      ... on MessageEvent {
        timestamp
      }
    }
  }
  executionPlan {
    steps {
      key
    }
  }
  environmentConfigYaml
  mode
}
'''


def _get_runs_data(result, run_id):
    for run_data in result.data['pipeline']['runs']:
        if run_data['runId'] == run_id:
            # so caller can delete keys
            return copy.deepcopy(run_data)

    raise Exception('nope')


def test_get_runs_over_graphql(snapshot):
    context = define_context()
    payload_one = sync_execute_get_run_log_data(
        {
            'executionParams': {
                'selector': {'name': 'multi_mode_with_resources'},
                'mode': 'add_mode',
                'environmentConfigData': {'resources': {'op': {'config': 2}}},
            }
        },
        context=context,
    )
    run_id_one = payload_one['runId']

    payload_two = sync_execute_get_run_log_data(
        {
            'executionParams': {
                'selector': {'name': 'multi_mode_with_resources'},
                'mode': 'add_mode',
                'environmentConfigData': {'resources': {'op': {'config': 3}}},
            }
        },
        #
        #     'pipeline': {'name': 'multi_mode_with_resources'},
        #     'mode': 'add_mode',
        #     'environmentConfigData': {'resources': {'op': {'config': 3}}},
        # },
        context=context,
    )

    run_id_two = payload_two['runId']

    result = execute_dagster_graphql(
        context, RUNS_QUERY, variables={'name': 'multi_mode_with_resources'}
    )

    run_one_data = _get_runs_data(result, run_id_one)
    assert run_one_data['logs']
    del run_one_data['logs']  # unstable between invokes
    del run_one_data['runId']  # unstable between invokes
    snapshot.assert_match(run_one_data)

    run_two_data = _get_runs_data(result, run_id_two)
    assert run_two_data['logs']
    del run_two_data['logs']  # unstable between invokes
    del run_two_data['runId']  # unstable between invokes
    snapshot.assert_match(run_two_data)
