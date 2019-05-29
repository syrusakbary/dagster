from abc import ABCMeta, abstractmethod
from collections import defaultdict, namedtuple

import six

from dagster import check
from dagster.utils import camelcase
from dagster.core.errors import DagsterInvalidDefinitionError

from .input import InputDefinition
from .output import OutputDefinition
from .utils import DEFAULT_OUTPUT, struct_to_string


class SolidInstance(namedtuple('Solid', 'name alias resource_mapper_fn')):
    '''
    A solid identifier in a dependency structure. Allows supplying parameters to the solid,
    like the alias.

    Args:
        name (str): Name of the solid in the pipeline to instance.
        alias (Optional[str]):
            Name for this instance of the solid. Necessary when there are multiple instances
            of the same solid.

    Example:

        .. code-block:: python

            pipeline = Pipeline(
                solids=[solid_1, solid_2]
                dependencies={
                    SolidInstance('solid_2', alias='other_name') : {
                        'input_name' : DependencyDefinition('solid_2'),
                    },
                    'solid_1' : {
                        'input_name': DependencyDefinition('other_name'),
                    },
                }
            )
    '''

    def __new__(cls, name, alias=None, resource_mapper_fn=None):
        name = check.str_param(name, 'name')
        alias = check.opt_str_param(alias, 'alias')
        resource_mapper_fn = check.opt_callable_param(
            resource_mapper_fn, 'resource_mapper_fn', SolidInstance.default_resource_mapper_fn
        )
        return super(cls, SolidInstance).__new__(cls, name, alias, resource_mapper_fn)

    @staticmethod
    def default_resource_mapper_fn(_resource_names, resource_deps):
        return {r: r for r in resource_deps}


class Solid(object):
    '''
    Solid instance within a pipeline. Defined by its name inside the pipeline.

    Attributes:
        name (str):
            Name of the solid inside the pipeline. Must be unique per-pipeline.
        definition (SolidDefinition):
            Definition of the solid.
    '''

    def __init__(self, name, definition, resource_mapper_fn, parent=None):
        from .solid import ISolidDefinition, CompositeSolidDefinition

        self.name = check.str_param(name, 'name')
        self.definition = check.inst_param(definition, 'definition', ISolidDefinition)
        self.resource_mapper_fn = check.callable_param(resource_mapper_fn, 'resource_mapper_fn')
        self.parent = check.opt_inst_param(parent, 'parent', CompositeSolidDefinition)

        input_handles = {}
        for name, input_def in self.definition.input_dict.items():
            input_handles[name] = SolidInputHandle(self, input_def)

        self._input_handles = input_handles

        output_handles = {}
        for name, output_def in self.definition.output_dict.items():
            output_handles[name] = SolidOutputHandle(self, output_def)

        self._output_handles = output_handles

    def input_handles(self):
        return self._input_handles.values()

    def output_handles(self):
        return self._output_handles.values()

    def input_handle(self, name):
        check.str_param(name, 'name')
        return self._input_handles[name]

    def output_handle(self, name):
        check.str_param(name, 'name')
        return self._output_handles[name]

    def has_input(self, name):
        return self.definition.has_input(name)

    def input_def_named(self, name):
        return self.definition.input_def_named(name)

    def has_output(self, name):
        return self.definition.has_output(name)

    def output_def_named(self, name):
        return self.definition.output_def_named(name)

    @property
    def input_dict(self):
        return self.definition.input_dict

    @property
    def output_dict(self):
        return self.definition.output_dict

    @property
    def step_metadata_fn(self):
        return self.definition.step_metadata_fn

    def parent_maps_input(self, input_name):
        if self.parent is None:
            return False

        return self.parent.mapped_input(self.name, input_name) is not None

    def parent_mapped_input(self, input_name):
        return self.parent.mapped_input(self.name, input_name)


class SolidHandle(namedtuple('_SolidHandle', 'name definition_name parent')):
    def __new__(cls, name, definition_name, parent):
        return super(SolidHandle, cls).__new__(
            cls,
            check.str_param(name, 'name'),
            check.opt_str_param(definition_name, 'definition_name'),
            check.opt_inst_param(parent, 'parent', SolidHandle),
        )

    def __str__(self):
        return self.to_string()

    def to_string(self):
        # Return unique name of the solid and its lineage (omits solid definition names)
        return self.parent.to_string() + '.' + self.name if self.parent else self.name

    def camelcase(self):
        return (
            self.parent.camelcase() + '.' + camelcase(self.name)
            if self.parent
            else camelcase(self.name)
        )


class SolidInputHandle(namedtuple('_SolidInputHandle', 'solid input_def')):
    def __new__(cls, solid, input_def):
        return super(SolidInputHandle, cls).__new__(
            cls,
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(input_def, 'input_def', InputDefinition),
        )

    def _inner_str(self):
        return struct_to_string(
            'SolidInputHandle',
            solid_name=self.solid.name,
            definition_name=self.solid.definition.name,
            input_name=self.input_def.name,
        )

    def __str__(self):
        return self._inner_str()

    def __repr__(self):
        return self._inner_str()

    def __hash__(self):
        return hash((self.solid.name, self.input_def.name))

    def __eq__(self, other):
        return self.solid.name == other.solid.name and self.input_def.name == other.input_def.name


class SolidOutputHandle(namedtuple('_SolidOutputHandle', 'solid output_def')):
    def __new__(cls, solid, output_def):
        return super(SolidOutputHandle, cls).__new__(
            cls,
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(output_def, 'output_def', OutputDefinition),
        )

    def _inner_str(self):
        return struct_to_string(
            'SolidOutputHandle',
            solid_name=self.solid.name,
            definition_name=self.solid.definition.name,
            output_name=self.output_def.name,
        )

    def __str__(self):
        return self._inner_str()

    def __repr__(self):
        return self._inner_str()

    def __hash__(self):
        return hash((self.solid.name, self.output_def.name))

    def __eq__(self, other):
        return self.solid.name == other.solid.name and self.output_def.name == other.output_def.name


class InputToOutputHandleDict(defaultdict):
    def __init__(self):
        defaultdict.__init__(self, list)

    def __getitem__(self, key):
        check.inst_param(key, 'key', SolidInputHandle)
        return defaultdict.__getitem__(self, key)

    def __setitem__(self, key, val):
        check.inst_param(key, 'key', SolidInputHandle)
        check.list_param(val, 'val', of_type=SolidOutputHandle)
        return defaultdict.__setitem__(self, key, val)


def _create_handle_dict(solid_dict, dep_dict):
    check.dict_param(solid_dict, 'solid_dict', key_type=str, value_type=Solid)
    check.two_dim_dict_param(dep_dict, 'dep_dict', value_type=IDependencyDefinition)

    handle_dict = InputToOutputHandleDict()

    for solid_name, input_dict in dep_dict.items():
        for input_name, dep_def in input_dict.items():
            for dep in dep_def.get_definitions():
                from_solid = solid_dict[solid_name]
                to_solid = solid_dict[dep.solid]
                handle_dict[from_solid.input_handle(input_name)].append(
                    to_solid.output_handle(dep.output)
                )

    return handle_dict


class DependencyStructure(object):
    @staticmethod
    def from_definitions(solids, dep_dict):
        return DependencyStructure(_create_handle_dict(solids, dep_dict))

    def __init__(self, handle_dict):
        self._handle_dict = check.inst_param(handle_dict, 'handle_dict', InputToOutputHandleDict)

    def deps_of_solid(self, solid_name):
        check.str_param(solid_name, 'solid_name')

        return list(handles[1] for handles in self.__gen_deps_of_solid(solid_name))

    def deps_of_solid_with_input(self, solid_name):
        check.str_param(solid_name, 'solid_name')
        result = defaultdict(list)
        for input_handle, output_handle in self.__gen_deps_of_solid(solid_name):
            result[input_handle].append(output_handle)
        return result

    def __gen_deps_of_solid(self, solid_name):
        for input_handle, output_handles in self._handle_dict.items():
            if input_handle.solid.name == solid_name:
                for output_handle in output_handles:
                    yield (input_handle, output_handle)

    def depended_by_of_solid(self, solid_name):
        check.str_param(solid_name, 'solid_name')
        result = defaultdict(list)
        for input_handle, output_handles in self._handle_dict.items():
            for output_handle in output_handles:
                if output_handle.solid.name == solid_name:
                    result[output_handle].append(input_handle)

        return result

    def has_singular_dep(self, solid_input_handle):
        check.inst_param(solid_input_handle, 'solid_input_handle', SolidInputHandle)
        return len(self._handle_dict.get(solid_input_handle, [])) == 1

    def get_singular_dep(self, solid_input_handle):
        check.inst_param(solid_input_handle, 'solid_input_handle', SolidInputHandle)
        deps = self._handle_dict[solid_input_handle]
        check.invariant(
            len(deps) == 1,
            'Can not call get_singular_dep when number of deps is not 1, got {n}'.format(
                n=len(deps)
            ),
        )
        return deps[0]

    def has_deps(self, solid_input_handle):
        check.inst_param(solid_input_handle, 'solid_input_handle', SolidInputHandle)
        return solid_input_handle in self._handle_dict

    def get_deps(self, solid_input_handle):
        check.inst_param(solid_input_handle, 'solid_input_handle', SolidInputHandle)
        return self._handle_dict[solid_input_handle]

    def input_handles(self):
        return list(self._handle_dict.keys())

    def items(self):
        return self._handle_dict.items()


class IDependencyDefinition(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def get_definitions(self):
        pass


class DependencyDefinition(
    namedtuple('_DependencyDefinition', 'solid output description'), IDependencyDefinition
):
    '''Dependency definitions represent an edge in the DAG of solids. This object is
    used with a dictionary structure (whose keys represent solid/input where the dependency
    comes from) so this object only contains the target dependency information.

    Args:
        solid (str):
            The name of the solid that is the target of the dependency.
            This is the solid where the value passed between the solids
            comes from.
        output (str):
            The name of the output that is the target of the dependency.
            Defaults to "result", the default output name of solids with a single output.
        description (str):
            Description of this dependency. Optional.
    '''

    def __new__(cls, solid, output=DEFAULT_OUTPUT, description=None):
        return super(DependencyDefinition, cls).__new__(
            cls,
            check.str_param(solid, 'solid'),
            check.str_param(output, 'output'),
            check.opt_str_param(description, 'description'),
        )

    def get_definitions(self):
        return [self]


class MultiDependencyDefinition(
    namedtuple('_MultiDependencyDefinition', 'dependencies'), IDependencyDefinition
):
    def __new__(cls, dependencies):
        deps = check.list_param(dependencies, 'dependencies', of_type=DependencyDefinition)
        seen = {}
        for dep in deps:
            key = dep.solid + ':' + dep.output
            if key in seen:
                raise DagsterInvalidDefinitionError(
                    'Duplicate dependencies on solid "{dep.solid}" output "{dep.output}" '
                    'used in the same MultiDependencyDefinition.'.format(dep=dep)
                )
            seen[key] = True

        return super(MultiDependencyDefinition, cls).__new__(cls, deps)

    def get_definitions(self):
        return self.dependencies
