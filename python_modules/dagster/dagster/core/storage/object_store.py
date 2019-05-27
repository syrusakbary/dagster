import logging
import os
import shutil

from abc import ABCMeta, abstractmethod

import six

from dagster import check
from dagster.core.types.marshal import SerDe
from dagster.utils import mkdir_p


class ObjectStore(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def set_object(self, key, obj, serde=None):
        pass

    @abstractmethod
    def get_object(self, key, serde=None):
        pass

    @abstractmethod
    def has_object(self, key):
        pass

    @abstractmethod
    def rm_object(self, key):
        pass

    @abstractmethod
    def cp_object(self, src, dst):
        pass

    @abstractmethod
    def uri_for_key(self, key, protocol=None):
        pass


class FileSystemObjectStore(ObjectStore):  # pylint: disable=no-init
    def set_object(self, key, obj, serde=None):
        check.str_param(key, 'key')
        # cannot check obj since could be arbitrary Python object
        check.opt_inst_param(serde, 'serde', SerDe)

        if os.path.exists(key):
            logging.warning('Removing existing path {path}'.format(path=key))
            os.unlink(key)

        # Ensure path exists
        mkdir_p(os.path.dirname(key))

        if serde:
            serde.serialize_to_file(obj, key)
        else:
            with open(key, 'wb') as f:
                f.write(obj)

        return key

    def get_object(self, key, serde=None):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        if serde:
            return serde.deserialize_from_file(key)
        else:
            with open(key, 'rb') as f:
                return f.read()

    def has_object(self, key):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        return os.path.exists(key)

    def rm_object(self, key):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        if not self.has_object(key):
            return
        if os.path.isfile(key):
            os.unlink(key)
        elif os.path.isdir(key):
            shutil.rmtree(key)

    def cp_object(self, src, dst):
        check.invariant(not os.path.exists(dst), 'Path already exists {}'.format(dst))

        # Ensure output path exists
        mkdir_p(os.path.dirname(dst))

        if os.path.isfile(src):
            shutil.copy(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            check.failed('should not get here')

    def uri_for_key(self, key, protocol=None):
        check.str_param(key, 'key')
        protocol = check.opt_str_param(protocol, 'protocol', default='file://')
        return protocol + '/' + key
