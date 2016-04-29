import json
import os
import tempfile
import shutil

import pytest
import mock
from click.testing import CliRunner

# By doing this import we make sure that the plugin is made available
# but the entry points loading inside gg.main.
# An alternative would we to set `PYTHONPATH=. py.test` (or something)
# but then that wouldn't test the entry point loading.
from gg.main import Config
from gg_start import start


@pytest.fixture()
def temp_configfile(request):
    tmp_dir = tempfile.mkdtemp('gg-start')
    fp = os.path.join(tmp_dir, 'state.json')

    with open(fp, 'w') as f:
        json.dump({}, f)

    def teardown():
        shutil.rmtree(tmp_dir)

    request.addfinalizer(teardown)
    return fp


def test_start(temp_configfile, mocker):
    mocked_popen = mocker.patch('subprocess.Popen')

    def pipe(args, **kwargs):
        res = mock.MagicMock()
        if args[1] == 'branch':
            res.communicate.return_value = b'master', b''
        elif args[1] == 'checkout':
            res.communicate.return_value = b'checked out', b''
        elif args[1] == 'rev-parse':
            res.communicate.return_value = b'gg-start-test', b''
        else:
            raise NotImplementedError(args)
        return res
    mocked_popen.side_effect = pipe

    runner = CliRunner()
    config = Config()
    config.configfile = temp_configfile
    result = runner.invoke(start, [''], input='foo "bar"\n', obj=config)
    assert result.exit_code == 0
    assert not result.exception

    with open(temp_configfile) as f:
        saved = json.load(f)

        assert 'gg-start-test:foo-bar' in saved
        assert saved['gg-start-test:foo-bar']['description'] == 'foo "bar"'
        assert saved['gg-start-test:foo-bar']['date']


def test_start_weird_description(temp_configfile, mocker):
    mocked_popen = mocker.patch('subprocess.Popen')

    def pipe(args, **kwargs):
        res = mock.MagicMock()
        if args[1] == 'branch':
            res.communicate.return_value = b'master', b''
        elif args[1] == 'checkout':
            res.communicate.return_value = b'checked out', b''
        elif args[1] == 'rev-parse':
            res.communicate.return_value = b'gg-start-test', b''
        else:
            raise NotImplementedError(args)
        return res
    mocked_popen.side_effect = pipe

    runner = CliRunner()
    config = Config()
    config.configfile = temp_configfile
    summary = "  a!@#$%^&*()_+{}[/]-= ;:   --> ==>  ---  `foo`   ,. <bar>     "
    result = runner.invoke(start, [''], input=summary + '\n', obj=config)
    assert result.exit_code == 0
    assert not result.exception

    expected_branchname = 'a_+-foo-bar'

    with open(temp_configfile) as f:
        saved = json.load(f)

        key = 'gg-start-test:' + expected_branchname
        assert key in saved
        assert saved[key]['description'] == summary.strip()


def test_start_not_a_git_repo(temp_configfile, mocker):
    mocked_popen = mocker.patch('subprocess.Popen')

    def pipe(args, **kwargs):
        res = mock.MagicMock()
        if args[1] == 'branch':
            res.communicate.return_value = b'', b'Not a git repository'
        else:
            raise NotImplementedError(args)
        return res
    mocked_popen.side_effect = pipe

    runner = CliRunner()
    config = Config()
    config.configfile = temp_configfile
    result = runner.invoke(start, [''], obj=config)
    assert result.exit_code == 1
