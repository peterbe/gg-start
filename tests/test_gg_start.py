import json
import os
import tempfile
import shutil

import git
import pytest
from click.testing import CliRunner

# By doing this import we make sure that the plugin is made available
# but the entry points loading inside gg.main.
# An alternative would we to set `PYTHONPATH=. py.test` (or something)
# but then that wouldn't test the entry point loading.
from gg.main import Config
from gg_start import start


@pytest.yield_fixture
def temp_configfile():
    tmp_dir = tempfile.mkdtemp('gg-start')
    fp = os.path.join(tmp_dir, 'state.json')
    with open(fp, 'w') as f:
        json.dump({}, f)
    yield fp
    shutil.rmtree(tmp_dir)


def test_start(temp_configfile, mocker):
    mocked_git = mocker.patch('git.Repo')
    mocked_git().working_dir = 'gg-start-test'

    runner = CliRunner()
    config = Config()
    config.configfile = temp_configfile
    result = runner.invoke(start, [''], input='foo "bar"\n', obj=config)
    assert result.exit_code == 0
    assert not result.exception

    mocked_git().create_head.assert_called_with('foo-bar')
    mocked_git().create_head().checkout.assert_called_with()

    with open(temp_configfile) as f:
        saved = json.load(f)

        assert 'gg-start-test:foo-bar' in saved
        assert saved['gg-start-test:foo-bar']['description'] == 'foo "bar"'
        assert saved['gg-start-test:foo-bar']['date']


def test_start_weird_description(temp_configfile, mocker):
    mocked_git = mocker.patch('git.Repo')
    mocked_git().working_dir = 'gg-start-test'

    runner = CliRunner()
    config = Config()
    config.configfile = temp_configfile
    summary = "  a!@#$%^&*()_+{}[/]-= ;:   --> ==>  ---  `foo`   ,. <bar>     "
    result = runner.invoke(start, [''], input=summary + '\n', obj=config)
    assert result.exit_code == 0
    assert not result.exception

    expected_branchname = 'a_+-foo-bar'
    mocked_git().create_head.assert_called_with(expected_branchname)
    mocked_git().create_head().checkout.assert_called_with()

    with open(temp_configfile) as f:
        saved = json.load(f)

        key = 'gg-start-test:' + expected_branchname
        assert key in saved
        assert saved[key]['description'] == summary.strip()


def test_start_not_a_git_repo(temp_configfile, mocker):
    mocked_git = mocker.patch('git.Repo')

    mocked_git.side_effect = git.InvalidGitRepositoryError('/some/place')

    runner = CliRunner()
    config = Config()
    config.configfile = temp_configfile
    result = runner.invoke(start, [''], obj=config)
    assert result.exit_code == 1
    assert '"/some/place" is not a git repository' in result.output
    assert 'Aborted!' in result.output
    assert result.exception
