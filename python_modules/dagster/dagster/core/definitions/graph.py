from dagster import check
from .dependency import Solid, SolidInstance, DependencyDefinition, SolidOutputHandle
from .output import OutputDefinition
from .solid import SolidDefinition


class DepGraphValue:
    def __init__(self, bound_solid_node, output_def):
        self.bound_solid_node = check.inst_param(
            bound_solid_node, 'bound_solid_node', BoundDepSolidNode
        )
        self.output_def = check.inst_param(output_def, 'output_def', OutputDefinition)

    @property
    def from_solid(self):
        return self.bound_solid_node.solid_node.solid

    @property
    def output_handle(self):
        return SolidOutputHandle(self.bound_solid_node.solid_node.solid, self.output_def)


class BoundDepSolidNode:
    def __init__(self, solid_node, input_values):
        self.solid_node = solid_node
        self.input_values = input_values

    @property
    def solid_name(self):
        return self.solid_node.solid.name


class DepSolidNode:
    def __init__(self, solid):
        self.solid = check.inst_param(solid, 'solid', Solid)

    @property
    def solid_def(self):
        return self.solid.definition

    def __call__(self, *args, **kwargs):
        check.invariant(not args, 'only kwargs for now')

        check.dict_param(kwargs, 'kwargs', key_type=str, value_type=DepGraphValue)

        # When this is called the solid is bounded to set of inputs

        bound_dep_solid_node = BoundDepSolidNode(self, input_values=kwargs)

        if len(self.solid_def.output_defs) > 1:
            return tuple(
                [
                    DepGraphValue(bound_dep_solid_node, output_def)
                    for output_def in self.solid_def.output_defs
                ]
            )
        elif len(self.solid_def.output_defs) == 1:
            graph_value = DepGraphValue(bound_dep_solid_node, self.solid_def.output_defs[0])
            return graph_value
        else:
            return None


class DepSolidDefNode:
    def __init__(self, solid_def):
        self.solid_def = check.inst_param(solid_def, 'solid_def', SolidDefinition)

    def __call__(self, *args, **kwargs):
        return DepSolidNode(Solid(self.solid_def.name, self.solid_def))(*args, **kwargs)

    def __getattr__(self, attr, *args, **kwargs):
        check.str_param(attr, 'attr')
        check.invariant(not args, 'no args')
        check.invariant(not kwargs, 'no kwargs')

        return DepSolidNode(Solid(attr, self.solid_def))

    def alias(self, name):
        return DepSolidNode(Solid(name, self.solid_def))


def construct_dep_dict(bound_solid_nodes):
    deps = {}
    for bsn in bound_solid_nodes:
        solid_instance = SolidInstance(
            bsn.solid_node.solid.definition.name, alias=bsn.solid_node.solid.name
        )
        deps[solid_instance] = {}
        for input_name, input_value in bsn.input_values.items():
            deps[solid_instance][input_name] = DependencyDefinition(
                input_value.from_solid.name, input_value.output_def.name
            )
    return deps


def from_dep_func(fn):
    value_or_values = fn()

    value_tuple = (
        value_or_values if isinstance(value_or_values, tuple) else tuple([value_or_values])
    )

    all_values_dict = {}

    def recurse(graph_value):
        if graph_value.output_handle in all_values_dict:
            return

        all_values_dict[graph_value.output_handle] = graph_value

        for input_graph_value in graph_value.bound_solid_node.input_values.values():
            recurse(input_graph_value)

    for value in value_tuple:
        # This is for the multiple output case
        if isinstance(value, tuple):
            for t_value in value:
                recurse(t_value)
        else:
            recurse(value)

    bsn_dict = {}

    for value in all_values_dict.values():
        bsn_dict[value.bound_solid_node.solid_name] = value.bound_solid_node

    bsns = list(bsn_dict.values())

    solid_defs = list(set([bsn.solid_node.solid_def for bsn in bsns]))

    return solid_defs, construct_dep_dict(bsns)
