from click.testing import CliRunner

from dagit.cli import ui
from dagster.utils import file_relative_path


def test_invoke_ui():
    runner = CliRunner()
    result = runner.invoke(ui, ['--version'])
    assert 'dagit, version' in result.output


def test_invoke_with_bad_module_name_in_repository_yaml():
    runner = CliRunner()
    result = runner.invoke(ui, ['-y', file_relative_path(__file__, 'repository_bad_module.yaml')])
    assert 'ModuleNotFoundError' in str(result)


def test_invoke_with_bad_module_name_in_cli():
    runner = CliRunner()
    result = runner.invoke(ui, ['-m', 'kjdfkdjfd', '-n', 'foo'])
    assert 'ModuleNotFoundError' in str(result)
