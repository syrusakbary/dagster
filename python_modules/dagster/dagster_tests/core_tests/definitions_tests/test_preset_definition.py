import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    PipelineDefinition,
    lambda_solid,
    solid,
    Field,
    Bool,
    Dict,
    execute_pipeline,
    DagsterExecutionStepExecutionError,
    PresetDefinition,
    ModeDefinition,
)
from dagster.utils import script_relative_path


def test_presets():
    @solid(config_field=Field(Dict(fields={'error': Field(Bool)})))
    def can_fail(context):
        if context.solid_config['error']:
            raise Exception('I did an error')
        return 'cool'

    @lambda_solid
    def always_fail():
        raise Exception('I always do this')

    pipeline = PipelineDefinition(
        name='simple',
        solids=[can_fail, always_fail],
        preset_definitions=[
            PresetDefinition(
                'passing',
                environment_files=[script_relative_path('pass_env.yaml')],
                solid_subset=['can_fail'],
            ),
            PresetDefinition(
                'failing_1',
                environment_files=[script_relative_path('fail_env.yaml')],
                solid_subset=['can_fail'],
            ),
            PresetDefinition(
                'failing_2', environment_files=[script_relative_path('pass_env.yaml')]
            ),
            PresetDefinition(
                'invalid_1', environment_files=[script_relative_path('not_a_file.yaml')]
            ),
            PresetDefinition(
                'invalid_2',
                environment_files=[script_relative_path('test_repository_definition.py')],
            ),
        ],
    )

    execute_pipeline(**(pipeline.get_preset('passing')))

    with pytest.raises(DagsterExecutionStepExecutionError):
        execute_pipeline(**(pipeline.get_preset('failing_1')))

    with pytest.raises(DagsterExecutionStepExecutionError):
        execute_pipeline(**(pipeline.get_preset('failing_2')))

    with pytest.raises(DagsterInvalidDefinitionError, match="not_a_file.yaml"):
        execute_pipeline(**(pipeline.get_preset('invalid_1')))

    with pytest.raises(DagsterInvariantViolationError, match="error attempting to parse yaml"):
        execute_pipeline(**(pipeline.get_preset('invalid_2')))

    with pytest.raises(DagsterInvariantViolationError, match="Could not find preset"):
        execute_pipeline(**(pipeline.get_preset('not_failing')))


def test_invalid_preset():
    @lambda_solid
    def lil_solid():
        return ';)'

    with pytest.raises(DagsterInvalidDefinitionError, match='mode "mode_b" which is not defined'):
        PipelineDefinition(
            name="preset_modes",
            solids=[lil_solid],
            mode_definitions=[ModeDefinition(name="mode_a")],
            preset_definitions=[PresetDefinition(name="preset_b", mode="mode_b")],
        )
