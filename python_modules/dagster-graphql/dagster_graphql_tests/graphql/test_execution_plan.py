import uuid
from dagster import check
from dagster.core.storage.intermediate_store import FileSystemIntermediateStore
from dagster.utils import merge_dicts, script_relative_path
from dagster.utils.test import get_temp_file_name


from .setup import (
    define_context,
    execute_dagster_graphql,
    csv_hello_world_solids_config,
    csv_hello_world_solids_config_fs_storage,
    PoorMansDataFrame,
)


EXECUTION_PLAN_QUERY = '''
query PipelineQuery($environmentConfigData: EnvironmentConfigData, $pipeline: ExecutionSelector!, $mode: String!) {
  executionPlan(environmentConfigData: $environmentConfigData, pipeline: $pipeline, mode: $mode) {
    __typename
    ... on ExecutionPlan {
      pipeline { name }
      steps {
        key
        solidHandleID
        kind
        inputs {
          name
          type {
            name
          }
          dependsOn {
            key
          }
        }
        outputs {
          name
          type {
            name
          }
        }
        metadata {
          key
          value
        }
      }
    }
    ... on PipelineNotFoundError {
        pipelineName
    }
  }
}
'''

EXECUTE_PLAN_QUERY = '''
mutation ($executionParams: ExecutionParams!) {
    executePlan(executionParams: $executionParams) {
        __typename
        ... on ExecutePlanSuccess {
            pipeline { name }
            hasFailures
            stepEvents {
                __typename
                step {
                    key
                    metadata {
                       key
                       value
                    }
                }
                ... on ExecutionStepOutputEvent {
                    outputName
                    valueRepr
                }
                ... on StepMaterializationEvent {
                    materialization {
                        path
                        description
                    }
                }
                ... on ExecutionStepFailureEvent {
                    error {
                        message
                    }
                }
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
    }
}
'''


def get_nameset(llist):
    return {item['name'] for item in llist}


def get_named_thing(llist, name):
    for cn in llist:
        if cn['name'] == name:
            return cn

    check.failed('not found')


def test_success_whole_execution_plan(snapshot):
    run_id = str(uuid.uuid4())
    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': None,
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['step']['key']: step_event for step_event in query_result['stepEvents']
    }
    assert 'sum_solid.compute' in step_events
    assert 'sum_sq_solid.compute' in step_events

    snapshot.assert_match(result.data)
    store = FileSystemIntermediateStore(run_id)
    assert store.has_intermediate(None, 'sum_solid.compute')
    assert store.has_intermediate(None, 'sum_sq_solid.compute')


def test_success_whole_execution_plan_with_filesystem_config(snapshot):
    run_id = str(uuid.uuid4())
    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': merge_dicts(
                    csv_hello_world_solids_config(), {'storage': {'filesystem': {}}}
                ),
                'stepKeys': None,
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['step']['key']: step_event for step_event in query_result['stepEvents']
    }
    assert 'sum_solid.compute' in step_events
    assert 'sum_sq_solid.compute' in step_events

    snapshot.assert_match(result.data)
    store = FileSystemIntermediateStore(run_id)
    assert store.has_intermediate(None, 'sum_solid.compute')
    assert store.has_intermediate(None, 'sum_sq_solid.compute')


def test_success_whole_execution_plan_with_in_memory_config(snapshot):
    run_id = str(uuid.uuid4())
    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': merge_dicts(
                    csv_hello_world_solids_config(), {'storage': {'in_memory': {}}}
                ),
                'stepKeys': None,
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['step']['key']: step_event for step_event in query_result['stepEvents']
    }
    assert 'sum_solid.compute' in step_events
    assert 'sum_sq_solid.compute' in step_events

    snapshot.assert_match(result.data)
    store = FileSystemIntermediateStore(run_id)
    assert not store.has_intermediate(None, 'sum_solid.compute')
    assert not store.has_intermediate(None, 'sum_sq_solid.compute')


def test_successful_one_part_execute_plan(snapshot):
    run_id = str(uuid.uuid4())
    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': ['sum_solid.inputs.num.read', 'sum_solid.compute'],
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False

    step_events = query_result['stepEvents']
    # 0-2 are sum_solid.num.input_thunk
    assert step_events[3]['step']['key'] == 'sum_solid.compute'
    assert step_events[4]['__typename'] == 'ExecutionStepOutputEvent'
    assert step_events[4]['outputName'] == 'result'
    expected_value_repr = (
        '''[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3)]), '''
        '''OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7)])]'''
    )
    assert step_events[4]['valueRepr'] == expected_value_repr
    assert step_events[5]['__typename'] == 'ExecutionStepSuccessEvent'

    snapshot.assert_match(result.data)

    store = FileSystemIntermediateStore(run_id)
    assert store.has_intermediate(None, 'sum_solid.compute')
    assert (
        str(store.get_intermediate(None, 'sum_solid.compute', PoorMansDataFrame))
        == expected_value_repr
    )


def test_successful_two_part_execute_plan(snapshot):
    run_id = str(uuid.uuid4())
    result_one = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': ['sum_solid.inputs.num.read', 'sum_solid.compute'],
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    assert result_one.data['executePlan']['__typename'] == 'ExecutePlanSuccess'

    snapshot.assert_match(result_one.data)

    result_two = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': ['sum_sq_solid.compute'],
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    query_result = result_two.data['executePlan']
    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False
    step_events = query_result['stepEvents']
    assert step_events[0]['__typename'] == 'ExecutionStepStartEvent'
    assert step_events[0]['step']['key'] == 'sum_sq_solid.compute'
    assert step_events[1]['__typename'] == 'ExecutionStepOutputEvent'
    assert step_events[1]['outputName'] == 'result'
    assert step_events[2]['__typename'] == 'ExecutionStepSuccessEvent'

    snapshot.assert_match(result_two.data)

    expected_value_repr = (
        '''[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3), '''
        '''('sum_sq', 9)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7), '''
        '''('sum_sq', 49)])]'''
    )

    store = FileSystemIntermediateStore(run_id)
    assert store.has_intermediate(None, 'sum_sq_solid.compute')
    assert (
        str(store.get_intermediate(None, 'sum_sq_solid.compute', PoorMansDataFrame))
        == expected_value_repr
    )


def test_invalid_config_execute_plan(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': {
                    'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 384938439}}}}}
                },
                'stepKeys': [
                    'sum_solid.num.input_thunk',
                    'sum_solid.compute',
                    'sum_sq_solid.compute',
                ],
                'executionMetadata': {'runId': 'kdjkfjdfd'},
                'mode': 'default',
            }
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['executePlan']['__typename'] == 'PipelineConfigValidationInvalid'
    assert len(result.data['executePlan']['errors']) == 1
    assert (
        result.data['executePlan']['errors'][0]['message']
        == 'Value at path root:solids:sum_solid:inputs:num is not valid. Expected "Path"'
    )
    snapshot.assert_match(result.data)


def test_pipeline_not_found_error_execute_plan(snapshot):

    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'nope'},
                'environmentConfigData': {
                    'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 'ok'}}}}}
                },
                'stepKeys': [
                    'sum_solid.num.input_thunk',
                    'sum_solid.compute',
                    'sum_sq_solid.compute',
                ],
                'executionMetadata': {'runId': 'kdjkfjdfd'},
                'mode': 'default',
            }
        },
    )

    assert result.data['executePlan']['__typename'] == 'PipelineNotFoundError'
    assert result.data['executePlan']['pipelineName'] == 'nope'
    snapshot.assert_match(result.data)


def test_pipeline_with_execution_metadata(snapshot):
    environment_dict = {'solids': {'solid_metadata_creation': {'config': {'str_value': 'foobar'}}}}
    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        variables={
            'pipeline': {'name': 'pipeline_with_step_metadata'},
            'environmentConfigData': environment_dict,
            'mode': 'default',
        },
    )

    steps_data = result.data['executionPlan']['steps']
    assert len(steps_data) == 1
    step_data = steps_data[0]
    assert step_data['key'] == 'solid_metadata_creation.compute'
    assert len(step_data['metadata']) == 1
    assert step_data['metadata'][0] == {'key': 'computed', 'value': 'foobar1'}

    snapshot.assert_match(result.data)


def test_basic_execute_plan_with_materialization():
    with get_temp_file_name() as out_csv_path:

        environment_dict = {
            'solids': {
                'sum_solid': {
                    'inputs': {'num': script_relative_path('../data/num.csv')},
                    'outputs': [{'result': out_csv_path}],
                }
            }
        }

        result = execute_dagster_graphql(
            define_context(),
            EXECUTION_PLAN_QUERY,
            variables={
                'pipeline': {'name': 'csv_hello_world'},
                'environmentConfigData': environment_dict,
                'mode': 'default',
            },
        )

        steps_data = result.data['executionPlan']['steps']

        assert [step_data['key'] for step_data in steps_data] == [
            'sum_solid.inputs.num.read',
            'sum_solid.compute',
            'sum_solid.outputs.result.materialize.0',
            'sum_solid.outputs.result.materialize.join',
            'sum_sq_solid.compute',
        ]

        result = execute_dagster_graphql(
            define_context(),
            EXECUTE_PLAN_QUERY,
            variables={
                'executionParams': {
                    'selector': {'name': 'csv_hello_world'},
                    'environmentConfigData': environment_dict,
                    'stepKeys': [
                        'sum_solid.inputs.num.read',
                        'sum_solid.compute',
                        'sum_solid.outputs.result.materialize.0',
                        'sum_solid.outputs.result.materialize.join',
                        'sum_sq_solid.compute',
                    ],
                    'executionMetadata': {'runId': 'kdjkfjdfd'},
                    'mode': 'default',
                }
            },
        )

        assert result.data

        step_mat_event = None

        for message in result.data['executePlan']['stepEvents']:
            if message['__typename'] == 'StepMaterializationEvent':
                # ensure only one event
                assert step_mat_event is None
                step_mat_event = message

        # ensure only one event
        assert step_mat_event
        assert step_mat_event['materialization']['path'] == out_csv_path
