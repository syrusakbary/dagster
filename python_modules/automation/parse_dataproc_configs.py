from __future__ import print_function

import os
import pprint

import requests

from printer import IndentingBufferPrinter

SCALAR_TYPES = {
    'string': 'String',
    'boolean': 'Bool',
    'number': 'Int',
    'enumeration': 'String',
    'integer': 'Int',
}


class List:
    def __init__(self, inner_type):
        self.inner_type = inner_type


class Enum:
    def __init__(self, name, enum_names, enum_descriptions):
        self.name = name
        self.enum_names = enum_names
        self.enum_descriptions = enum_descriptions

    def write(self, printer):
        printer.line(self.name.title() + ' = Enum(')
        with printer.with_indent():
            printer.line('name=\'{}\','.format(self.name.title()))
            printer.line('enum_values=[')
            with printer.with_indent():
                if self.enum_descriptions:
                    for name, value in zip(self.enum_names, self.enum_descriptions):
                        printer.line('EnumValue(\'{}\', description=\'{}\'),'.format(name, value))
                else:
                    for name in self.enum_names:
                        printer.line('EnumValue(\'{}\'),'.format(name))

            printer.line('],')
        printer.line(')')


class Field:
    '''Field represents a field type that we're going to write out as a dagster config field, once
    we've pre-processed all custom types
    '''

    def __init__(self, fields, is_optional, description):
        self.fields = fields
        self.is_optional = is_optional
        self.description = description

    def __repr__(self):
        return 'Field(%s, %s, %s)' % (
            pprint.pformat(self.fields),
            str(self.is_optional),
            self.description,
        )

    def _print_fields(self, printer):
        # Scalars
        if isinstance(self.fields, str):
            printer.line(self.fields + ',')
        # Enums
        elif isinstance(self.fields, Enum):
            printer.line(self.fields.name + ',')
        # Lists
        elif isinstance(self.fields, List):
            printer.line('List(')
            self.fields.inner_type.write(printer, field_wrapped=False)
            printer.line('),')
        # Dicts
        else:
            printer.line('Dict(')
            with printer.with_indent():
                printer.line('fields={')
                with printer.with_indent():
                    for (k, v) in self.fields.items():
                        # We need to skip "output" fields which are API responses, not queries
                        if 'Output only' in v.description:
                            continue

                        # This v is a terminal scalar type, print directly
                        if isinstance(v, str):
                            printer.line("'{}': {},".format(k, v))

                        # Recurse nested fields
                        else:
                            with printer.with_indent():
                                printer.append("'{}': ".format(k))
                            v.write(printer)
                            printer.append(',')
                printer.line('},')
            printer.line('),')

    def write(self, printer, field_wrapped=True):
        '''Use field_wrapped=False for Lists that should not be wrapped in Field()
        '''
        if not field_wrapped:
            self._print_fields(printer)
            return printer.read()

        printer.append('Field(')
        printer.line('')
        with printer.with_indent():
            self._print_fields(printer)

            # Print description
            if self.description:
                printer.block(
                    self.description.replace("'", "\\'") + "''',", initial_indent="description='''"
                )

            # Print is_optional=True/False if defined; if not defined, default to True
            printer.line(
                'is_optional=%s,' % str(self.is_optional if self.is_optional is not None else True)
            )
        printer.line(')')
        return printer.read()


class ConfigParser:
    def __init__(self, api_url, base_path):

        json_schema = requests.get(api_url).json()
        self.schemas = json_schema.get('schemas')
        self.base_path = base_path

        # Stashing these in a global so that we can write out after we're done constructing configs
        self.all_enums = {}

    def _write_config(self, base_field, suffix):
        with IndentingBufferPrinter() as printer:
            printer.write_header()
            printer.line('from dagster import Bool, Dict, Field, Int, List, PermissiveDict, String')
            printer.blank_line()

            # Optionally write enum includes
            if self.all_enums:
                printer.line(
                    'from .types_{} import {}'.format(suffix, ', '.join(self.all_enums.keys()))
                )
                printer.blank_line()

            printer.line('def define_%s_config():' % suffix)
            with printer.with_indent():
                printer.append('return ')
                base_field.write(printer)

            with open(os.path.join(self.base_path, 'configs_%s.py' % suffix), 'wb') as f:
                f.write(printer.read().strip().encode())

    def _write_enums(self, suffix):
        if not self.all_enums:
            return

        with IndentingBufferPrinter() as printer:
            printer.write_header()
            printer.line('from dagster import Enum, EnumValue')
            printer.blank_line()
            for enum in self.all_enums:
                self.all_enums[enum].write(printer)
                printer.blank_line()

            with open(os.path.join(self.base_path, 'types_%s.py' % suffix), 'wb') as f:
                f.write(printer.read().strip().encode())

    def _parse_object(self, obj, name=None, depth=0, enum_descriptions=None):
        # This is a reference to another object that we should substitute by recursing
        if '$ref' in obj:
            name = obj['$ref']
            return self._parse_object(self.schemas.get(name), name, depth + 1)

        # Print type tree
        prefix = '|' + ('-' * 4 * depth) + ' ' if depth > 0 else ''
        print(prefix + (name or obj.get('type')))

        # Switch on object type
        obj_type = obj.get('type')

        # Handle enums
        if 'enum' in obj:
            # I think this is a bug in the API JSON spec where enum descriptions are a level higher
            # than they should be for type "Component" and the name isn't there
            if name is None:
                name = 'Component'

            enum = Enum(name, obj['enum'], enum_descriptions or obj.get('enumDescriptions'))
            self.all_enums[name] = enum
            fields = enum

        # Handle dicts / objects
        elif obj_type == 'object':
            # This is a generic k:v map
            if 'additionalProperties' in obj:
                fields = 'PermissiveDict()'
            else:
                fields = {
                    k: self._parse_object(v, k, depth + 1) for k, v in obj['properties'].items()
                }

        # Handle arrays
        elif obj_type == 'array':
            fields = List(
                self._parse_object(
                    obj.get('items'), None, depth + 1, enum_descriptions=obj.get('enumDescriptions')
                )
            )

        # Scalars
        elif obj_type in SCALAR_TYPES:
            fields = SCALAR_TYPES.get(obj_type)

        # Should never get here
        else:
            raise Exception('unknown type: ', obj)

        return Field(fields, is_optional=None, description=obj.get('description'))

    def extract_schema_for_object(self, object_name, name):
        # Reset enums for this object
        self.all_enums = {}

        obj = self._parse_object(self.schemas.get(object_name), object_name)
        self._write_config(obj, name)
        self._write_enums(name)


if __name__ == '__main__':
    c = ConfigParser(
        api_url='https://www.googleapis.com/discovery/v1/apis/dataproc/v1/rest',
        base_path='libraries/dagster-gcp/dagster_gcp/dataproc/',
    )
    c.extract_schema_for_object('Job', 'dataproc_job')

    print('\n\n')

    c.extract_schema_for_object('ClusterConfig', 'dataproc_cluster')
