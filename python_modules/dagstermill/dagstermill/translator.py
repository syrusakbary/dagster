DAGSTER_TRANSLATOR = None


def get_dagster_translator():
    global DAGSTER_TRANSLATOR
    if DAGSTER_TRANSLATOR is not None:
        return DAGSTER_TRANSLATOR

    import papermill

    class DagsterTranslator(papermill.translators.PythonTranslator):
        @classmethod
        def codify(cls, parameters):
            assert 'dm_context' in parameters
            content = '{}\n'.format(cls.comment('Parameters'))
            content += '{}\n'.format('import json')
            content += '{}\n'.format(
                cls.assign(
                    'context',
                    'dm.populate_context(json.loads(\'{dm_context}\'))'.format(
                        dm_context=parameters['dm_context']
                    ),
                )
            )

            for name, val in parameters.items():
                if name == 'dm_context':
                    continue
                dm_unmarshal_call = 'dm.load_parameter("{name}", {val})'.format(
                    name=name, val='"{val}"'.format(val=val) if isinstance(val, str) else val
                )
                content += '{}\n'.format(cls.assign(name, dm_unmarshal_call))

            return content

    DAGSTER_TRANSLATOR = DagsterTranslator
    return DagsterTranslator
