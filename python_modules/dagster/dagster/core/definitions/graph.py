from dagster import check
from .dependency import Solid, SolidInstance, DependencyDefinition
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


class BoundDepSolidNode:
    def __init__(self, graph, solid_node, input_values):
        self.graph = graph
        self.solid_node = solid_node
        self.input_values = input_values

    @property
    def solid_name(self):
        return self.solid_node.solid.name


class DepSolidNode:
    def __init__(self, graph, solid):
        self.graph = check.inst_param(graph, 'graph', DepGraphBuilder)
        self.solid = check.inst_param(solid, 'solid', Solid)

    @property
    def solid_def(self):
        return self.solid.definition

    def __call__(self, *args, **kwargs):
        check.invariant(not args, 'only kwargs for now')

        check.dict_param(kwargs, 'kwargs', key_type=str, value_type=DepGraphValue)

        # When this is called the solid is bounded to set of inputs

        bound_dep_solid_node = BoundDepSolidNode(self.graph, self, input_values=kwargs)

        self.graph.bound_solid_nodes.append(bound_dep_solid_node)

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


class DepGraphBuilder:
    def __init__(self, solid_defs):
        self._solid_defs = {}
        # TODO: figure out instances
        for solid_def in solid_defs:
            self._solid_defs[solid_def.name] = solid_def

        # self.solids = list(self._solid_dict.values())
        self.bound_solid_nodes = []

    def __getattr__(self, attr, *args, **kwargs):
        check.str_param(attr, 'attr')
        check.invariant(not args, 'no args')
        check.invariant(not kwargs, 'no kwargs')

        return DepSolidDefNode(self, self._solid_defs[attr])


class DepSolidDefNode:
    def __init__(self, graph, solid_def):
        self.graph = graph
        self.solid_def = check.inst_param(solid_def, 'solid_def', SolidDefinition)

    def __call__(self, *args, **kwargs):
        return DepSolidNode(self.graph, Solid(self.solid_def.name, self.solid_def))(*args, **kwargs)

    def __getattr__(self, attr, *args, **kwargs):
        check.str_param(attr, 'attr')
        check.invariant(not args, 'no args')
        check.invariant(not kwargs, 'no kwargs')

        return DepSolidNode(self.graph, Solid(attr, self.solid_def))

    def alias(self, name):
        return DepSolidNode(self.graph, Solid(name, self.solid_def))


def construct_dep_dict(graph):
    deps = {}
    for bsn in graph.bound_solid_nodes:
        solid_instance = SolidInstance(
            bsn.solid_node.solid.definition.name, alias=bsn.solid_node.solid.name
        )
        deps[solid_instance] = {}
        for input_name, input_value in bsn.input_values.items():
            deps[solid_instance][input_name] = DependencyDefinition(
                input_value.from_solid.name, input_value.output_def.name
            )
    return deps


def from_dep_func(solid_defs, fn):
    graph = DepGraphBuilder(solid_defs=solid_defs)
    fn(graph)
    return construct_dep_dict(graph)
