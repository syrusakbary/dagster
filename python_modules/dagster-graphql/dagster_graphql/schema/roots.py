from dagster.core.execution.api import ExecutionSelector

from dagster_graphql import dauphin
from dagster_graphql.implementation.execution import (
    ExecutionMetadata,
    ExecutionParams,
    do_execute_plan,
    get_pipeline_run_observable,
    start_pipeline_execution,
)
from dagster_graphql.implementation.fetch_types import get_config_type, get_runtime_type
from dagster_graphql.implementation.fetch_pipelines import (
    get_pipeline,
    get_pipeline_or_raise,
    get_pipelines,
    get_pipelines_or_raise,
)
from dagster_graphql.implementation.fetch_runs import (
    get_execution_plan,
    get_run,
    get_runs,
    validate_pipeline_config,
)


class DauphinQuery(dauphin.ObjectType):
    class Meta:
        name = 'Query'

    version = dauphin.NonNull(dauphin.String)
    pipelineOrError = dauphin.Field(
        dauphin.NonNull('PipelineOrError'), params=dauphin.NonNull('ExecutionSelector')
    )
    pipeline = dauphin.Field(
        dauphin.NonNull('Pipeline'), params=dauphin.NonNull('ExecutionSelector')
    )
    pipelinesOrError = dauphin.NonNull('PipelinesOrError')
    pipelines = dauphin.Field(dauphin.NonNull('PipelineConnection'))

    configTypeOrError = dauphin.Field(
        dauphin.NonNull('ConfigTypeOrError'),
        pipelineName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        configTypeName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        mode=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )

    runtimeTypeOrError = dauphin.Field(
        dauphin.NonNull('RuntimeTypeOrError'),
        pipelineName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        runtimeTypeName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )
    pipelineRuns = dauphin.non_null_list('PipelineRun')

    pipelineRunOrError = dauphin.Field(
        dauphin.NonNull('PipelineRunOrError'), runId=dauphin.NonNull(dauphin.ID)
    )

    isPipelineConfigValid = dauphin.Field(
        dauphin.NonNull('PipelineConfigValidationResult'),
        args={
            'pipeline': dauphin.Argument(dauphin.NonNull('ExecutionSelector')),
            'environmentConfigData': dauphin.Argument('EnvironmentConfigData'),
            'mode': dauphin.Argument(dauphin.NonNull(dauphin.String)),
        },
    )

    executionPlan = dauphin.Field(
        dauphin.NonNull('ExecutionPlanResult'),
        args={
            'pipeline': dauphin.Argument(dauphin.NonNull('ExecutionSelector')),
            'environmentConfigData': dauphin.Argument('EnvironmentConfigData'),
            'mode': dauphin.Argument(dauphin.NonNull(dauphin.String)),
        },
    )

    def resolve_configTypeOrError(self, graphene_info, **kwargs):
        return get_config_type(
            graphene_info, kwargs['pipelineName'], kwargs['configTypeName'], kwargs.get('mode')
        )

    def resolve_runtimeTypeOrError(self, graphene_info, **kwargs):
        return get_runtime_type(graphene_info, kwargs['pipelineName'], kwargs['runtimeTypeName'])

    def resolve_version(self, graphene_info):
        return graphene_info.context.version

    def resolve_pipelineOrError(self, graphene_info, **kwargs):
        return get_pipeline(graphene_info, kwargs['params'].to_selector())

    def resolve_pipeline(self, graphene_info, **kwargs):
        return get_pipeline_or_raise(graphene_info, kwargs['params'].to_selector())

    def resolve_pipelinesOrError(self, graphene_info):
        return get_pipelines(graphene_info)

    def resolve_pipelines(self, graphene_info):
        return get_pipelines_or_raise(graphene_info)

    def resolve_pipelineRuns(self, graphene_info):
        return get_runs(graphene_info)

    def resolve_pipelineRunOrError(self, graphene_info, runId):
        return get_run(graphene_info, runId)

    def resolve_isPipelineConfigValid(self, graphene_info, pipeline, **kwargs):
        return validate_pipeline_config(
            graphene_info,
            pipeline.to_selector(),
            kwargs.get('environmentConfigData'),
            kwargs.get('mode'),
        )

    def resolve_executionPlan(self, graphene_info, pipeline, **kwargs):
        return get_execution_plan(
            graphene_info,
            pipeline.to_selector(),
            kwargs.get('environmentConfigData'),
            kwargs.get('mode'),
        )


class DauphinStepOutputHandle(dauphin.InputObjectType):
    class Meta:
        name = 'StepOutputHandle'

    stepKey = dauphin.NonNull(dauphin.String)
    outputName = dauphin.NonNull(dauphin.String)


class DauphinReexecutionConfig(dauphin.InputObjectType):
    class Meta:
        name = 'ReexecutionConfig'

    previousRunId = dauphin.NonNull(dauphin.String)
    stepOutputHandles = dauphin.non_null_list(DauphinStepOutputHandle)

    def to_reexecution_config(self):
        from dagster.core.execution.config import ReexecutionConfig
        from dagster.core.execution.plan.objects import StepOutputHandle

        return ReexecutionConfig(
            self.previousRunId,
            list(map(lambda g: StepOutputHandle(g.stepKey, g.outputName), self.stepOutputHandles)),
        )


class DauphinStartPipelineExecutionMutation(dauphin.Mutation):
    class Meta:
        name = 'StartPipelineExecutionMutation'

    class Arguments:
        executionParams = dauphin.NonNull('ExecutionParams')
        reexecutionConfig = dauphin.Argument('ReexecutionConfig')

    Output = dauphin.NonNull('StartPipelineExecutionResult')

    def mutate(self, graphene_info, **kwargs):
        return start_pipeline_execution(
            graphene_info,
            execution_params=create_execution_params(kwargs['executionParams']),
            reexecution_config=kwargs['reexecutionConfig'].to_reexecution_config()
            if 'reexecutionConfig' in kwargs
            else None,
        )


class DauphinExecutionTag(dauphin.InputObjectType):
    class Meta:
        name = 'ExecutionTag'

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)


class DauphinMarshalledInput(dauphin.InputObjectType):
    class Meta:
        name = 'MarshalledInput'

    input_name = dauphin.NonNull(dauphin.String)
    key = dauphin.NonNull(dauphin.String)


class DauphinMarshalledOutput(dauphin.InputObjectType):
    class Meta:
        name = 'MarshalledOutput'

    output_name = dauphin.NonNull(dauphin.String)
    key = dauphin.NonNull(dauphin.String)


class DauphinStepExecution(dauphin.InputObjectType):
    class Meta:
        name = 'StepExecution'

    stepKey = dauphin.NonNull(dauphin.String)
    marshalledInputs = dauphin.List(dauphin.NonNull(DauphinMarshalledInput))
    marshalledOutputs = dauphin.List(dauphin.NonNull(DauphinMarshalledOutput))


class DauphinExecutionMetadata(dauphin.InputObjectType):
    class Meta:
        name = 'ExecutionMetadata'

    runId = dauphin.String()
    tags = dauphin.List(dauphin.NonNull(DauphinExecutionTag))


def create_execution_params(graphql_execution_params):
    return ExecutionParams(
        selector=graphql_execution_params['selector'].to_selector(),
        environment_dict=graphql_execution_params.get('environmentConfigData'),
        mode=graphql_execution_params['mode'],
        execution_metadata=create_execution_metadata(
            graphql_execution_params.get('executionMetadata')
        ),
        step_keys=graphql_execution_params.get('stepKeys'),
    )


def create_execution_metadata(graphql_execution_metadata):
    return (
        ExecutionMetadata(
            graphql_execution_metadata.get('runId'),
            {t['key']: t['value'] for t in graphql_execution_metadata.get('tags', [])},
        )
        if graphql_execution_metadata
        else ExecutionMetadata(run_id=None, tags={})
    )


class DauphinExecutePlan(dauphin.Mutation):
    class Meta:
        name = 'ExecutePlan'

    class Arguments:
        executionParams = dauphin.NonNull('ExecutionParams')

    Output = dauphin.NonNull('ExecutePlanResult')

    def mutate(self, graphene_info, **kwargs):
        return do_execute_plan(graphene_info, create_execution_params(kwargs['executionParams']))


class DauphinMutation(dauphin.ObjectType):
    class Meta:
        name = 'Mutation'

    start_pipeline_execution = DauphinStartPipelineExecutionMutation.Field()
    execute_plan = DauphinExecutePlan.Field()


class DauphinSubscription(dauphin.ObjectType):
    class Meta:
        name = 'Subscription'

    pipelineRunLogs = dauphin.Field(
        dauphin.NonNull('PipelineRunLogsSubscriptionPayload'),
        runId=dauphin.Argument(dauphin.NonNull(dauphin.ID)),
        after=dauphin.Argument('Cursor'),
    )

    def resolve_pipelineRunLogs(self, graphene_info, runId, after=None):
        return get_pipeline_run_observable(graphene_info, runId, after)


class DauphinEnvironmentConfigData(dauphin.GenericScalar, dauphin.Scalar):
    class Meta:
        name = 'EnvironmentConfigData'
        description = '''This type is used when passing in a configuration object
        for pipeline configuration. This is any-typed in the GraphQL type system,
        but must conform to the constraints of the dagster config type system'''


class DauphinExecutionParams(dauphin.InputObjectType):
    class Meta:
        name = 'ExecutionParams'

    selector = dauphin.NonNull('ExecutionSelector')
    environmentConfigData = dauphin.Field('EnvironmentConfigData')
    mode = dauphin.NonNull(dauphin.String)
    executionMetadata = dauphin.Field('ExecutionMetadata')
    stepKeys = dauphin.Field(dauphin.List(dauphin.NonNull(dauphin.String)))


class DauphinExecutionSelector(dauphin.InputObjectType):
    class Meta:
        name = 'ExecutionSelector'
        description = '''This type represents the fields necessary to identify a
        pipeline or pipeline subset.'''

    name = dauphin.NonNull(dauphin.String)
    solidSubset = dauphin.List(dauphin.NonNull(dauphin.String))

    def to_selector(self):
        return ExecutionSelector(self.name, self.solidSubset)
