from dagster import check

from dagster.core.definitions import (
    ExpectationDefinition,
    ExpectationResult,
    InputDefinition,
    OutputDefinition,
    Result,
    Solid,
    SolidHandle,
)

from dagster.core.errors import DagsterExpectationFailedError, DagsterInvariantViolationError

from dagster.core.execution.context.system import SystemStepExecutionContext

from dagster.core.execution.context.expectation import ExpectationExecutionContext

from dagster.core.system_config.objects import EnvironmentConfig

from .objects import (
    ExecutionStep,
    ExecutionValueSubplan,
    StepInput,
    StepOutput,
    StepOutputHandle,
    StepKind,
)

from .utility import create_joining_subplan

EXPECTATION_INPUT = 'expectation_input'
EXPECTATION_VALUE_OUTPUT = 'expectation_value'


def _create_expectation_lambda(solid, inout_def, expectation_def, internal_output_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(expectation_def, 'expectations_def', ExpectationDefinition)
    check.str_param(internal_output_name, 'internal_output_name')

    def _do_expectation(expectation_context, inputs):
        check.inst_param(expectation_context, 'step_context', SystemStepExecutionContext)
        value = inputs[EXPECTATION_INPUT]
        expectation_context = expectation_context.for_expectation(inout_def, expectation_def)
        expt_result = expectation_def.expectation_fn(
            ExpectationExecutionContext(expectation_context), value
        )

        if not isinstance(expt_result, ExpectationResult):
            raise DagsterInvariantViolationError(
                (
                    'Expectation for solid {solid_name} on {desc_key} {inout_name} '
                    'did not return an ExpectationResult'.format(
                        solid_name=solid.name,
                        desc_key=inout_def.descriptive_key,
                        inout_name=inout_def.name,
                    )
                )
            )

        if expt_result.success:
            expectation_context.log.debug(
                'Expectation {key} succeeded on {value}.'.format(
                    key=expectation_context.step.key, value=value
                )
            )
            yield expt_result
            yield Result(output_name=internal_output_name, value=inputs[EXPECTATION_INPUT])
        else:
            expectation_context.log.debug(
                'Expectation {key} failed on {value}.'.format(
                    key=expectation_context.step.key, value=value
                )
            )
            raise DagsterExpectationFailedError(expectation_context, value)

    return _do_expectation


def create_expectations_subplan(
    pipeline_name, solid, inout_def, prev_step_output_handle, kind, handle
):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(kind, 'kind', StepKind)

    input_expect_steps = []
    for expectation_def in inout_def.expectations:
        expect_step = create_expectation_step(
            pipeline_name=pipeline_name,
            solid=solid,
            expectation_def=expectation_def,
            key_suffix='{desc_key}.{inout_name}.expectation.{expectation_name}'.format(
                desc_key=inout_def.descriptive_key,
                inout_name=inout_def.name,
                expectation_name=expectation_def.name,
            ),
            kind=kind,
            prev_step_output_handle=prev_step_output_handle,
            inout_def=inout_def,
            handle=handle,
        )
        input_expect_steps.append(expect_step)

    return create_joining_subplan(
        pipeline_name,
        solid,
        '{desc_key}.{inout_name}.expectations.join'.format(
            desc_key=inout_def.descriptive_key, inout_name=inout_def.name
        ),
        input_expect_steps,
        EXPECTATION_VALUE_OUTPUT,
        handle,
    )


def create_expectation_step(
    pipeline_name,
    solid,
    expectation_def,
    key_suffix,
    kind,
    prev_step_output_handle,
    inout_def,
    handle,
):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(expectation_def, 'expectation_def', ExpectationDefinition)
    check.str_param(key_suffix, 'key_suffix')
    check.inst_param(kind, 'kind', StepKind)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.opt_inst_param(handle, 'handle', SolidHandle)

    value_type = inout_def.runtime_type

    return ExecutionStep(
        pipeline_name=pipeline_name,
        key_suffix=key_suffix,
        step_inputs=[
            StepInput(
                name=EXPECTATION_INPUT,
                runtime_type=value_type,
                prev_output_handle=prev_step_output_handle,
            )
        ],
        step_outputs=[
            # Expectation value output is optional since we omit if the expectation fails
            StepOutput(name=EXPECTATION_VALUE_OUTPUT, runtime_type=value_type, optional=True)
        ],
        compute_fn=_create_expectation_lambda(
            solid, inout_def, expectation_def, EXPECTATION_VALUE_OUTPUT
        ),
        kind=kind,
        solid_handle=handle,
        logging_tags={
            'expectation': expectation_def.name,
            inout_def.descriptive_key: inout_def.name,
        },
    )


def decorate_with_expectations(
    pipeline_name, environment_config, solid, transform_step, output_def, handle
):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(transform_step, 'transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.opt_inst_param(handle, 'handle', SolidHandle)

    terminal_step_output_handle = StepOutputHandle.from_step(transform_step, output_def.name)

    if environment_config.expectations.evaluate and output_def.expectations:
        return create_expectations_subplan(
            pipeline_name,
            solid,
            output_def,
            terminal_step_output_handle,
            kind=StepKind.OUTPUT_EXPECTATION,
            handle=handle,
        )
    else:
        return ExecutionValueSubplan.empty(terminal_step_output_handle)
