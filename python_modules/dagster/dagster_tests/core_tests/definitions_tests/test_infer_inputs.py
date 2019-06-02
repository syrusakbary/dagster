import sys
import pytest

from dagster import lambda_solid, solid, Int, DagsterInvalidDefinitionError

from dagster.core.definitions.decorators import infer_input_definitions_for_solid


def test_no_context():
    def nope():
        pass

    with pytest.raises(DagsterInvalidDefinitionError):
        infer_input_definitions_for_solid('nope', nope)


def test_wrong_var():
    # pylint: disable=unused-argument
    def nope(kdjfkd):
        pass

    with pytest.raises(DagsterInvalidDefinitionError):
        infer_input_definitions_for_solid('nope', nope)


def test_infer_raw_inputs():
    def add_one(_context, num):
        return num + 1

    input_defs = infer_input_definitions_for_solid('add_one', add_one)

    assert len(input_defs) == 1
    assert input_defs[0].name == 'num'


def py3_only(fn):
    return pytest.mark.skipif(sys.version_info < (3, 6), reason='Type Annotations')(fn)


@py3_only
def test_infer_typed_input():
    def add_one(_context, num: Int):
        return num + 1

    input_defs = infer_input_definitions_for_solid('add_one', add_one)

    assert len(input_defs) == 1
    assert input_defs[0].name == 'num'
    assert input_defs[0].runtime_type.name == 'Int'


def test_single_input():
    @solid
    def add_one(_context, num):
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == 'num'
    assert add_one.input_defs[0].runtime_type.name == 'Any'


@py3_only
def test_single_typed_input():
    @solid
    def add_one(_context, num: Int):
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == 'num'
    assert add_one.input_defs[0].runtime_type.name == 'Int'


def test_double_input():
    @solid
    def add(_context, num_one, num_two):
        return num_one + num_two

    assert add
    assert len(add.input_defs) == 2
    assert add.input_defs[0].name == 'num_one'
    assert add.input_defs[0].runtime_type.name == 'Any'

    assert add.input_defs[1].name == 'num_two'
    assert add.input_defs[1].runtime_type.name == 'Any'


@py3_only
def test_double_typed_input():
    @solid
    def add(_context, num_one: Int, num_two: Int):
        return num_one + num_two

    assert add
    assert len(add.input_defs) == 2
    assert add.input_defs[0].name == 'num_one'
    assert add.input_defs[0].runtime_type.name == 'Int'

    assert add.input_defs[1].name == 'num_two'
    assert add.input_defs[1].runtime_type.name == 'Int'


def test_noop_lambda_solid():
    @lambda_solid
    def noop():
        pass

    assert noop
    assert len(noop.input_defs) == 0
    assert len(noop.output_defs) == 1


def test_one_arg_lambda_solid():
    @lambda_solid
    def one_arg(num):
        return num

    assert one_arg
    assert len(one_arg.input_defs) == 1
    assert one_arg.input_defs[0].name == 'num'
    assert one_arg.input_defs[0].runtime_type.name == 'Any'
    assert len(one_arg.output_defs) == 1


@py3_only
def test_one_arg_typed_lambda_solid():
    @lambda_solid
    def one_arg(num: Int):
        return num

    assert one_arg
    assert len(one_arg.input_defs) == 1
    assert one_arg.input_defs[0].name == 'num'
    assert one_arg.input_defs[0].runtime_type.name == 'Int'
    assert len(one_arg.output_defs) == 1


@py3_only
def test_single_typed_input_and_output():
    @solid
    def add_one(_context, num: Int) -> Int:
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == 'num'
    assert add_one.input_defs[0].runtime_type.name == 'Int'

    assert len(add_one.output_defs) == 1
    assert add_one.output_defs[0].runtime_type.name == 'Int'
