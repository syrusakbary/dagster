# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot, GenericRepr


snapshots = Snapshot()

snapshots['test_presets_on_examples 1'] = GenericRepr("<graphql.execution.base.ExecutionResult object at 0x100000000>")

snapshots['test_presets_on_examples 2'] = GenericRepr("<graphql.execution.base.ExecutionResult object at 0x100000000>")

snapshots['test_presets_on_examples 3'] = GenericRepr("<graphql.execution.base.ExecutionResult object at 0x100000000>")

snapshots['test_presets_on_examples 4'] = GenericRepr("<graphql.execution.base.ExecutionResult object at 0x100000000>")

snapshots['test_presets_on_examples 5'] = GenericRepr("<graphql.execution.base.ExecutionResult object at 0x100000000>")

snapshots['test_presets_on_examples 6'] = GenericRepr("<graphql.execution.base.ExecutionResult object at 0x100000000>")

snapshots['test_presets_on_examples 7'] = GenericRepr("<graphql.execution.base.ExecutionResult object at 0x100000000>")

snapshots['test_presets_on_examples 8'] = GenericRepr("<graphql.execution.base.ExecutionResult object at 0x100000000>")

snapshots['test_presets_on_examples 9'] = GenericRepr("<graphql.execution.base.ExecutionResult object at 0x100000000>")

snapshots['test_presets_on_examples 10'] = GenericRepr("<graphql.execution.base.ExecutionResult object at 0x100000000>")

snapshots['test_presets_on_examples 11'] = GenericRepr("<graphql.execution.base.ExecutionResult object at 0x100000000>")

snapshots['test_basic_preset_query_with_presets 1'] = {
    'pipeline': {
        'name': 'csv_hello_world',
        'presets': [
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''solids:
  sum_solid:
    inputs:
      num: data/num_prod.csv
''',
                'mode': 'default',
                'name': 'prod',
                'solidSubset': None
            },
            {
                '__typename': 'PipelinePreset',
                'environmentConfigYaml': '''solids:
  sum_solid:
    inputs:
      num: data/num.csv
''',
                'mode': 'default',
                'name': 'test',
                'solidSubset': None
            }
        ]
    }
}
