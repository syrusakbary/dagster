from dagster.utils import safe_isfile, script_relative_path, file_relative_path


def test_safe_isfile():
    assert safe_isfile(script_relative_path('test_safe_isfile.py'))
    assert not safe_isfile(script_relative_path('test_safe_isfile_foobar.py'))


def test_script_relative_path_file_relative_path_equiv():
    assert script_relative_path('foo') == file_relative_path(__file__, 'foo')
