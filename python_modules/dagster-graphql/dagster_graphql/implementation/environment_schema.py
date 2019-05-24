from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.execution.api import ExecutionSelector
from dagster.core.definitions.environment_schema import create_environment_schema
from .fetch_pipelines import get_dagster_pipeline_from_selector
from .utils import capture_dauphin_error, UserFacingGraphQLError


@capture_dauphin_error
def resolve_environment_schema_or_error(graphene_info, selector, mode):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    dagster_pipeline = get_dagster_pipeline_from_selector(graphene_info, selector)

    if not dagster_pipeline.has_mode_definition(mode):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ModeNotFoundError')(mode=mode, selector=selector)
        )

    return graphene_info.schema.type_named('EnvironmentSchema')(
        create_environment_schema(dagster_pipeline, mode)
    )
