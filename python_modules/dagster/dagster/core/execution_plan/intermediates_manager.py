from abc import ABCMeta, abstractmethod
from collections import namedtuple
import pickle

import six

from dagster import check

from dagster.core.files import FileStore


class StepOutputHandle(namedtuple('_StepOutputHandle', 'step_key output_name')):
    @staticmethod
    def from_step(step, output_name):
        from .objects import ExecutionStep

        check.inst_param(step, 'step', ExecutionStep)

        return StepOutputHandle(step.key, output_name)

    def __new__(cls, step_key, output_name):
        return super(StepOutputHandle, cls).__new__(
            cls,
            step_key=check.str_param(step_key, 'step_key'),
            output_name=check.str_param(output_name, 'output_name'),
        )


def read_pickle_file(path):
    check.str_param(path, 'path')
    with open(path, 'rb') as ff:
        return pickle.load(ff)


def write_pickle_file(path, value):
    check.str_param(path, 'path')
    with open(path, 'wb') as ff:
        return pickle.dump(value, ff)


class IntermediatesManager(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def read_step_output(self, run_id, step_output_handle):
        pass

    @abstractmethod
    def set_value(self, run_id, step_output_handle, value):
        pass

    @abstractmethod
    def has_value(self, run_id, step_output_handle):
        pass

    def all_inputs_covered(self, run_id, step):
        from .objects import ExecutionStep

        check.inst_param(step, 'step', ExecutionStep)
        for step_input in step.step_inputs:
            if not self.has_value(run_id, step_input.prev_output_handle):
                return False
        return True


from collections import defaultdict


class InMemoryIntermediatesManager(IntermediatesManager):
    def __init__(self):
        self.values = defaultdict(dict)

    def read_step_output(self, run_id, step_output_handle):
        check.str_param(run_id, 'run_id')
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        return self.values[run_id][step_output_handle]

    def set_value(self, run_id, step_output_handle, value):
        check.str_param(run_id, 'run_id')
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        self.values[run_id][step_output_handle] = value

    def has_value(self, run_id, step_output_handle):
        check.str_param(run_id, 'run_id')
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        return step_output_handle in self.values.get(run_id, {})


from dagster.core.runs import FileStorageBasedRunStorage

# TODO: This should go through persistence and serialization infrastructure
# Fixing this requires getting the type information (serialization_strategy is
# a property of runtime type) of the step output you are dealing with. As things
# are structured now we construct the inputs before execution. The fix to this
# will likely be to inject a different type of execution step that threads
# the manager
class FileSystemIntermediateManager(IntermediatesManager):
    def __init__(self, file_store):
        self._file_store = file_store

    def _get_path_comps(self, run_id, step_output_handle):
        return [
            run_id,
            'intermediates',
            step_output_handle.step_key,
            step_output_handle.output_name,
        ]

    def read_step_output(self, run_id, step_output_handle):
        print(f'Read step_output_handle {step_output_handle}')
        print(f'About to read path {self._get_path_comps(run_id, step_output_handle)}')

        check.str_param(run_id, 'run_id')
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        check.invariant(self.has_value(run_id, step_output_handle))

        with self._file_store.readable_binary_stream(
            *self._get_path_comps(run_id, step_output_handle)
        ) as ff:
            return pickle.load(ff)

    def set_value(self, run_id, step_output_handle, value):
        print(f'Write step_output_handle {step_output_handle}')
        print(f'About to write path {self._get_path_comps(run_id, step_output_handle)}')

        check.str_param(run_id, 'run_id')
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        check.invariant(not self.has_value(run_id, step_output_handle))

        with self._file_store.writeable_binary_stream(
            *self._get_path_comps(run_id, step_output_handle)
        ) as ff:
            pickle.dump(value, ff)

    def has_value(self, run_id, step_output_handle):
        return self._file_store.has_file(*self._get_path_comps(run_id, step_output_handle))
