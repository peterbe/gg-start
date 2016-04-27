import json
import os

import pytest
import mock
from click.testing import CliRunner

CONFIGFILE = '/tmp/test-gg-start.json'

# By doing this import we make sure that the plugin is made available
# but the entry points loading inside gg.main.
# An alternative would we to set `PYTHONPATH=. py.test` (or something)
# but then that wouldn't test the entry point loading.
from gg.main import Config
from gg_start import start


@pytest.fixture()
def configfile(request):

    with open(CONFIGFILE, 'w') as f:
        json.dump({}, f)

    def teardown():
        os.remove(CONFIGFILE)
    request.addfinalizer(teardown)


def test_start(configfile, mocker):
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
    config.configfile = CONFIGFILE
    result = runner.invoke(start, [''], input='foo "bar"\n', obj=config)
    assert result.exit_code == 0
    assert not result.exception

    with open(CONFIGFILE) as f:
        saved = json.load(f)

        assert 'gg-start-test:foo-bar' in saved
        assert saved['gg-start-test:foo-bar']['description'] == 'foo "bar"'
        assert saved['gg-start-test:foo-bar']['date']


def test_start_not_a_git_repo(configfile, mocker):
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
    config.configfile = CONFIGFILE
    result = runner.invoke(start, [''], obj=config)
    assert result.exit_code == 1
