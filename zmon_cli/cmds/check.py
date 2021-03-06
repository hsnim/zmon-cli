import yaml

import click

from clickclick import AliasedGroup, Action, ok

from zmon_cli.cmds.command import cli, get_client, yaml_output_option, pretty_json
from zmon_cli.output import dump_yaml, Output
from zmon_cli.client import ZmonArgumentError


@cli.group('check-definitions', cls=AliasedGroup)
@click.pass_obj
def check_definitions(obj):
    """Manage check definitions"""
    pass


@check_definitions.command('init')
@click.argument('yaml_file', type=click.File('wb'))
def init(yaml_file):
    """Initialize a new check definition YAML file"""
    # NOTE: sorted like FIELD_SORT_INDEX
    name = click.prompt('Check definition name', default='Example Check')
    owning_team = click.prompt('Team owning this check definition (i.e. your team)', default='Example Team')

    data = {
        'name': name,
        'owning_team': owning_team,
        'description': "Example ZMON check definition which returns a HTTP status code.\n" +
                       "You can write multiple lines here, including unicode ☺",
        'command': "# GET request on example.org and return HTTP status code\n" +
                   "http('http://example.org/', timeout=5).code()",
        'interval': 60,
        'entities': [{'type': 'GLOBAL'}],
        'status': 'ACTIVE'
    }

    yaml_file.write(dump_yaml(data).encode('utf-8'))
    ok()


@check_definitions.command('get')
@click.argument('check_id', type=int)
@click.pass_obj
@yaml_output_option
@pretty_json
def get_check_definition(obj, check_id, output, pretty):
    """Get a single check definition"""
    client = get_client(obj.config)

    with Output('Retrieving check definition ...', nl=True, output=output, pretty_json=pretty) as act:
        check = client.get_check_definition(check_id)

        keys = list(check.keys())
        for k in keys:
            if check[k] is None:
                del check[k]

        act.echo(check)


@check_definitions.command('update')
@click.argument('yaml_file', type=click.File('rb'))
@click.pass_obj
def update(obj, yaml_file):
    """Update a single check definition"""
    check = yaml.safe_load(yaml_file)

    check['last_modified_by'] = obj.get('user', 'unknown')

    client = get_client(obj.config)

    with Action('Updating check definition ...', nl=True) as act:
        try:
            check = client.update_check_definition(check)
            ok(client.check_definition_url(check))
        except ZmonArgumentError as e:
            act.error(str(e))


@check_definitions.command('delete')
@click.argument('check_id', type=int)
@click.pass_obj
def delete_check_definition(obj, check_id):
    """Delete an orphan check definition"""
    client = get_client(obj.config)

    with Action('Deleting check {} ...'.format(check_id)) as act:
        resp = client.delete_check_definition(check_id)

        if not resp.ok:
            act.error(resp.text)
