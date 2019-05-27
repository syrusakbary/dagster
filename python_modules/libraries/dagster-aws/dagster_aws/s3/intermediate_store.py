from dagster import RunStorageMode, check
from dagster.core.storage.intermediate_store import IntermediateStore

from .object_store import S3ObjectStore


class S3IntermediateStore(IntermediateStore):
    def __init__(self, s3_bucket, run_id, types_to_register=None):
        check.str_param(s3_bucket, 's3_bucket')
        check.str_param(run_id, 'run_id')
        self.storage_mode = RunStorageMode.S3
        self.sep = '/'

        super(S3IntermediateStore, self).__init__(
            S3ObjectStore(s3_bucket),
            root=self.get_run_files_path(None, run_id),
            sep=self.sep,
            types_to_register=types_to_register,
        )

    def copy_object_from_prev_run(
        self, context, previous_run_id, paths
    ):  # pylint: disable=unused-argument
        check.not_implemented('not supported: TODO for max. put issue number here')
