import tempfile
import os

import pytest

from dagster.core.types.marshal import PickleSerDe


# https://dev.azure.com/elementl/dagster/_build/results?buildId=2941
@pytest.mark.skipif(
    os.name == 'nt', reason='Azure pipelines does not let us use tempfile.NamedTemporaryFile'
)
def test_serde():
    serde = PickleSerDe()
    with tempfile.NamedTemporaryFile() as fd:
        serde.serialize_to_file('foo', fd.name)
        assert serde.deserialize_from_file(fd.name) == 'foo'
