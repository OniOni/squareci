import json
import os
import sys

import click
import requests

CIRCLE = 'https://circleci.com/api/v1.1/project/github'


def sub_dict(dict_, keys):
    return {
        k: v for k, v in dict_.items()
        if k in keys
    }


class CircleClient:

    def __init__(self, root=CIRCLE, project=None, auth=None):
        self.root = root
        self.project = project or os.environ['SQUARE_PROJECT']
        self.auth = (auth or os.environ['SQUARE_KEY'], '')


    def get(self, path='', limit=25, filter_='failed'):
        req = requests.get(
            f"{self.root}/{self.project}/{path}",
            params={'limit': limit, 'filter': filter_},
            auth=self.auth
        )

        return req.json()

    def get_failed_builds(self, limit=25):
        full = self.get(limit=limit)
        return [
            sub_dict(b, ('build_num', 'status', 'retries'))
            for b in full
        ]

    def get_failure_info(self, build_num):
        info = self.get(build_num)

        failure_info = {}
        for s in info['steps']:
            step_name = s['name']

            for a in s['actions']:
                if a['failed'] or a['status'] != "success":
                    failure_info = {
                        'step_name': step_name,
                        'action_name': a['name'],
                        'status': a['status'],
                        'infrastructure_fail': a['infrastructure_fail'],
                        'output': a.get('output_url')
                    }
                    break

            if failure_info:
                break
        else:
            print(json.dumps(info['steps']))
            sys.exit(-1)

        failure_info['branch'] = info['branch']

        return failure_info


def get_failure_counts(failure_info):
    data = {}

    for i in failure_info.values():
        k = f"{i['step_name']}/{i['action_name']}"
        if k not in data:
            data[k] = {
                'count': 0
            }

        data[k]['count'] += 1

    return data

def inspect_step(name, failure_info):
    return {
        k: v for k, v in failure_info.items()
        if name.lower() in v['action_name'].lower()
    }

@click.group()
@click.option('--project')
@click.option('--key')
@click.pass_context
def cli(ctx, project, key):
    ctx.obj = CircleClient(
        project=project,
        auth=key,
    )

@cli.command()
@click.argument('filter', required=True)
@click.option('--limit', default=25)
@click.pass_context
def inspect(ctx, filter, limit):
    c = ctx.obj
    builds = c.get_failed_builds(limit=limit)

    details = {
        b['build_num']: c.get_failure_info(b['build_num'])
        for b in builds
    }

    info = inspect_step(filter, details)
    click.echo(json.dumps(info))


@cli.command()
@click.option('--limit', default=25)
@click.pass_context
def stats(ctx, limit):
    c = ctx.obj
    builds = c.get_failed_builds(limit=limit)

    details = {
        b['build_num']: c.get_failure_info(b['build_num'])
        for b in builds
    }

    counts = get_failure_counts(details)
    counts = sorted(counts.items(), key=lambda x: x[1]['count'], reverse=True)

    click.echo(json.dumps(counts))


@cli.command()
@click.option('--limit', default=25)
@click.pass_context
def last(ctx, limit):
    c = ctx.obj
    builds = c.get_failed_builds(limit=limit)

    details = {
        b['build_num']: c.get_failure_info(b['build_num'])
        for b in builds
    }

    #counts = sorted(counts.items(), key=lambda x: x[1]['count'], reverse=True)

    click.echo(json.dumps(details))


if __name__ == '__main__':
    cli()
