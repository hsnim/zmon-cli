import yaml
from unittest.mock import MagicMock
from click.testing import CliRunner


from zmon_cli.main import cli
from zmon_cli.client import Zmon


def get_client(config):
    return Zmon('https://zmon-api', token='123')


def test_configure(monkeypatch):
    get = MagicMock()
    monkeypatch.setattr('requests.get', get)

    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ['configure', '-c', 'test.yaml'], catch_exceptions=False, input='https://example.org\n\n')

        assert 'Writing configuration' in result.output

        with open('test.yaml') as fd:
            data = yaml.safe_load(fd)

        assert data['url'] == 'https://example.org'
        assert 'token' not in data


def test_status(monkeypatch):
    get = MagicMock()
    get.return_value = {
        'workers': [{'name': 'foo', 'check_invocations': 12377, 'last_execution_time': 1}]
    }
    monkeypatch.setattr('zmon_cli.client.Zmon.status', get)
    monkeypatch.setattr('zmon_cli.cmds.command.get_client', get_client)

    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['status'], catch_exceptions=False)

        assert 'foo' in result.output
        assert '12377' in result.output
        assert 'd ago' in result.output


def test_status_zign(monkeypatch):
    get = MagicMock()
    get.return_value = {
        'workers': [{'name': 'foo', 'check_invocations': 12377, 'last_execution_time': 1}]
    }

    get_token = MagicMock()
    get_token.return_value = '1298'

    monkeypatch.setattr('zmon_cli.client.Zmon.status', get)
    monkeypatch.setattr('zmon_cli.cmds.command.get_client', get_client)
    monkeypatch.setattr('zign.api.get_token', get_token)

    runner = CliRunner()

    with runner.isolated_filesystem():
        with open('test.yaml', 'w') as fd:
            yaml.dump({'url': 'foo'}, fd)

        result = runner.invoke(cli, ['-c', 'test.yaml', 'status'], catch_exceptions=False)

        assert 'foo' in result.output
        assert '12377' in result.output
        assert 'd ago' in result.output

    get_token.assert_called_with('zmon', ['uid'])


def test_get_alert_definition(monkeypatch):
    get = MagicMock()
    get.return_value = {
        'id': 123, 'check_definition_id': 9, 'name': 'Test', 'condition': '>0', 'foo': None
    }

    monkeypatch.setattr('zmon_cli.client.Zmon.get_alert_definition', get)
    monkeypatch.setattr('zmon_cli.cmds.command.get_client', get_client)

    runner = CliRunner()

    with runner.isolated_filesystem():
        with open('test.yaml', 'w') as fd:
            yaml.dump({'url': 'foo', 'token': 123}, fd)

        result = runner.invoke(cli, ['-c', 'test.yaml', 'alert', 'get', '123'], catch_exceptions=False)

        assert 'id: 123\ncheck_definition_id: 9\nname: Test\ncondition: |-\n  >0' in result.output.rstrip()


def test_update_check_definition_invalid(monkeypatch):
    monkeypatch.setattr('zmon_cli.config.DEFAULT_CONFIG_FILE', 'test.yaml')

    runner = CliRunner()

    with runner.isolated_filesystem():
        with open('test.yaml', 'w') as fd:
            yaml.dump({'url': 'foo', 'token': '123'}, fd)

        with open('check.yaml', 'w') as fd:
            yaml.safe_dump({}, fd)

        result = runner.invoke(cli, ['-c', 'test.yaml', 'check', 'update', 'check.yaml'], catch_exceptions=False)

        assert 'owning_team' in result.output


def test_update_check_definition(monkeypatch):
    monkeypatch.setattr('zmon_cli.config.DEFAULT_CONFIG_FILE', 'test.yaml')

    post = MagicMock()
    post.return_value = {'id': 7}
    monkeypatch.setattr('zmon_cli.client.Zmon.update_check_definition', post)
    monkeypatch.setattr('zmon_cli.cmds.command.get_client', get_client)

    runner = CliRunner()

    with runner.isolated_filesystem():
        with open('test.yaml', 'w') as fd:
            yaml.dump({'url': 'foo', 'token': '123'}, fd)

        with open('check.yaml', 'w') as fd:
            yaml.safe_dump({'owning_team': 'myteam', 'command': 'do_stuff()'}, fd)

        result = runner.invoke(cli, ['-c', 'test.yaml', 'check', 'update', 'check.yaml'], catch_exceptions=False)

        assert '/check-definitions/view/7' in result.output
