import os
import sys
import logging
import argparse
import requests
from enum import Enum

_logger = logging.getLogger('bitrise')


def parse_args(cmdln_args):
    parser = argparse.ArgumentParser(
        description="Gets build data for a targeted app on Bitrise"
    )

    parser.add_argument(
        "--project",
        help="Use selected project",
        required=True,
        choices=['ios', 'android']
    )

    return parser.parse_args(args=cmdln_args)


class Status(Enum):
    NOT_FINISHED = 0
    SUCCESSFUL = 1
    FAILURE = 2
    ABORTED_FAILURE = 3
    ABORTED_SUCCESS = 4


class Bitrise:
    bitrise_api_token = str()
    bitrise_api_header = str()
    bitrise_app_slug = str()

    def __init__(self):
        self.set_config()

    def set_config(self):
        try:
            self.bitrise_api_token = os.environ['BITRISE_TOKEN']
            self.bitrise_api_header = {'Authorization': self.bitrise_api_token,
                                       'accept': 'application/json'}
        except KeyError:
            _logger.debug("set BITRISE_TOKEN")
            exit()

    def get_apps(self):
        resp = requests.get('https://api.bitrise.io/v0.1/apps',
                            headers=self.bitrise_api_header)
        if resp.status_code != 200:
            raise _logger.error('GET /apps/ {}'.format(resp.status_code))
        return resp.json()

    def get_app(self, project, apps):
        if project == "android":
            self.bitrise_app_slug = apps['data'][0]['slug']
        elif project == "ios":
            self.bitrise_app_slug = apps['data'][1]['slug']
        resp = requests.get('https://api.bitrise.io/v0.1/apps/{0}'
                            .format(self.bitrise_app_slug),
                            headers=self.bitrise_api_header)
        if resp.status_code != 200:
            raise _logger.error('GET /apps/ {}'.format(resp.status_code))
        return resp.json()

    def get_workflows(self, bitrise_app_slug):
        resp = \
            requests.get('https://api.bitrise.io/v0.1/apps/{0}'
                         '/build-workflows'.format(self.bitrise_app_slug),
                         headers=self.bitrise_api_header)
        if resp.status_code != 200:
            raise _logger.error('GET /apps/ {}'.format(resp.status_code))
        return resp.json()

    def get_builds(self, bitrise_app_slug):
        resp = \
            requests.get('https://api.bitrise.io/v0.1/apps/{0}'
                         '/builds'.format(self.bitrise_app_slug),
                         headers=self.bitrise_api_header)
        if resp.status_code != 200:
            raise _logger.error('GET /apps/ {}'.format(resp.status_code))
        return resp.json()

    def get_failure_count(self, builds):
        failure_count = int()
        for build in builds['data']:
            if(build['status'] == Status.FAILURE.value):
                failure_count += 1
        return failure_count


def main():
    args = parse_args(sys.argv[1:])
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    b = Bitrise()
    apps = b.get_apps()

    b.get_app(args.project, apps)

    '''Calling GET /apps/ will retrieve the first page of the app
       with size of 50.'''

    builds = b.get_builds(b.bitrise_app_slug)
    failures = b.get_failure_count(builds)

    print("Failure count: {0}".format(failures))


if __name__ == '__main__':
    main()
