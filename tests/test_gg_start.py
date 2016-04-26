import json
import os

import pytest
import mock
from click.testing import CliRunner

# gg.main sets up a pass_config decorator which depends on an instance
# of gg.main.Config. We can't easily mock or override that when invoking
# tests, so we manually create it and use the OS environment to set it.
# This isn't pretty but at the time of writing, Apr 2016, there is no
# other way to handle this more gracefully.
# Filed this as a reference: https://github.com/pallets/click/issues/565
CONFIG_FILE = '/tmp/test-gg-start.json'
os.environ['GG_DEFAULT_CONFIG_FILE'] = CONFIG_FILE

# By doing this import we make sure that the plugin is made available
# but the entry points loading inside gg.main.
# An alternative would we to set `PYTHONPATH=. py.test` (or something)
# but then that wouldn't test the entry point loading.
import gg.main  # NOQA
from gg_start import start


@pytest.fixture()
def configfile(request):

    with open(CONFIG_FILE, 'w') as f:
        json.dump({}, f)

    def teardown():
        os.remove(CONFIG_FILE)
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
    result = runner.invoke(start, [''], input='foo "bar"\n')
    assert result.exit_code == 0

    with open(CONFIG_FILE) as f:
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
    result = runner.invoke(start, [''])
    assert result.exit_code == 1
