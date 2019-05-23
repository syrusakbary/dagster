import inspect
from contextlib import contextmanager
from collections import namedtuple

from contextlib2 import ExitStack

from dagster import check
from dagster.core.types import Field, String
from dagster.core.types.field_utils import check_user_facing_opt_field_param
from dagster.core.errors import (
    DagsterResourceFunctionError,
    DagsterUserCodeExecutionError,
    user_code_error_boundary,
)


class ResourceDefinition(object):
    '''Resources are pipeline-scoped ways to make external resources (like database connections)
    available to solids during pipeline execution and clean up after execution resolves.

    Args:
        resource_fn (Callable[[InitResourceContext], Any]):
            User provided function to instantiate the resource. This resource will be available to
            solids via ``context.resources``
        config_field (Field):
            The type for the configuration data for this resource, passed to ``resource_fn`` via
            ``init_context.resource_config``
        description (str)
    '''

    def __init__(self, resource_fn, config_field=None, description=None):
        self.resource_fn = check.callable_param(resource_fn, 'resource_fn')
        self.config_field = check_user_facing_opt_field_param(
            config_field, 'config_field', 'of a ResourceDefinition or @resource'
        )
        self.description = check.opt_str_param(description, 'description')

    @staticmethod
    def none_resource(description=None):
        return ResourceDefinition(resource_fn=lambda _init_context: None, description=description)

    @staticmethod
    def string_resource(description=None):
        return ResourceDefinition(
            resource_fn=lambda init_context: init_context.resource_config,
            config_field=Field(String),
            description=description,
        )


def resource(config_field=None, description=None):
    '''A decorator for creating a resource. The decorated function will be used as the
    resource_fn in a ResourceDefinition.
    '''

    # This case is for when decorator is used bare, without arguments.
    # E.g. @resource versus @resource()
    if callable(config_field):
        return ResourceDefinition(resource_fn=config_field)

    def _wrap(resource_fn):
        return ResourceDefinition(resource_fn, config_field, description)

    return _wrap


class ResourcesBuilder:
    def __init__(self, resource_fn_map, exit_stack):
        self._resource_fn_map = check.dict_param(resource_fn_map, 'resource_fn_map')
        self._exit_stack = check.inst_param(exit_stack, 'exit_stack', ExitStack)
        self._resource_instances = dict()

    def _get_resource(self, resource_name):
        check.str_param(resource_name, 'resource_name')
        if resource_name in self._resource_instances:
            return self._resource_instances[resource_name]

        user_fn = self._resource_fn_map[resource_name]
        resource_obj = self._exit_stack.enter_context(
            user_code_context_manager(
                user_fn,
                DagsterResourceFunctionError,
                'Error executing resource_fn on ResourceDefinition {name}'.format(
                    name=resource_name
                ),
            )
        )
        self._resource_instances[resource_name] = resource_obj
        return resource_obj

    def build(self, mapper_fn, resource_deps):
        '''We dynamically create a type that has the resource keys as properties,
        to enable dotting into the resources from a context.

        For example, given:

        resources = {'foo': <some resource>, 'bar': <some other resource>}

        then this will create the type Resource(namedtuple('foo bar'))

        and then binds the specified resources into an instance of this object,
        which can be consumed as, e.g., context.resources.foo.
        '''
        check.callable_param(mapper_fn, 'mapper_fn')
        check.set_param(resource_deps, 'resource_deps', of_type=str)

        resource_names = list(self._resource_fn_map.keys())
        resource_map = mapper_fn(resource_names, resource_deps)

        resources = {
            mapped_name: self._get_resource(origin_name)
            for mapped_name, origin_name in resource_map.items()
        }
        print(resources, resource_map)
        resource_type = namedtuple('Resources', list(resources.keys()))
        return resource_type(**resources)


@contextmanager
def user_code_context_manager(user_fn, error_cls, msg):
    '''Wraps the output of a user provided function that may yield or return a value and
    returns a generator that asserts it only yields a single value.
    '''
    check.callable_param(user_fn, 'user_fn')
    check.subclass_param(error_cls, 'error_cls', DagsterUserCodeExecutionError)

    with user_code_error_boundary(error_cls, msg):
        thing_or_gen = user_fn()
        gen = _ensure_gen(thing_or_gen)

        try:
            thing = next(gen)
        except StopIteration:
            check.failed('Must yield one item. You did not yield anything.')

        yield thing

        stopped = False

        try:
            next(gen)
        except StopIteration:
            stopped = True

        check.invariant(stopped, 'Must yield one item. Yielded more than one item')


def _ensure_gen(thing_or_gen):
    if not inspect.isgenerator(thing_or_gen):

        def _gen_thing():
            yield thing_or_gen

        return _gen_thing()

    return thing_or_gen
