import re

import git
import click

from gg.utils import error_out, get_repo
from gg.state import save
from gg.main import cli, pass_config


@cli.command()
@click.argument('bugnumber', default='')
@pass_config
def start(config, bugnumber=''):
    try:
        repo = get_repo()
    except git.InvalidGitRepositoryError as exception:
        error_out('"{}" is not a git repository'.format(exception.args[0]))

    if bugnumber:
        raise NotImplementedError(bugnumber)
    else:
        summary = None
    if summary:
        description = input('Summary ["{}"]: '.format(summary)).strip()
    else:
        description = input('Summary: ').strip()

    branch_name = ''
    if bugnumber:
        branch_name = 'bug-{}-'.format(bugnumber)

    def clean_branch_name(string):
        string = re.sub('\s+', ' ', string)
        string = string.replace(' ', '-')
        string = string.replace('->', '-').replace('=>', '-')
        for each in '@%^&:\'"/(),[]{}!.?`$<>#*;=':
            string = string.replace(each, '')
        string = re.sub('-+', '-', string)
        return string.lower().strip()

    branch_name += clean_branch_name(description)

    new_branch = repo.create_head(branch_name)
    new_branch.checkout()
    if config.verbose:
        click.echo('Checkout out new branch: {}'.format(branch_name))

    save(
        config.configfile,
        description,
        branch_name,
        bugnumber=bugnumber
    )
