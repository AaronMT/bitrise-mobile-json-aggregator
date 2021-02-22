import os
import sys
import logging
import argparse
import requests
from enum import Enum

_logger = logging.getLogger(__name__)


def _init_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
    )


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


class Workflows(Enum):
    COMMON = "CommonBuild-UItest-XCUISmoketest"
    NEW_XCODE = "NewXcodeVersions"


class Bitrise:
    API_TOKEN = str()
    API_HEADER = str()
    APP_SLUG = str()

    def __init__(self):
        _init_logging()
        self.set_config()

    def set_config(self):
        try:
            self.API_TOKEN = os.environ['BITRISE_TOKEN']
            self.API_HEADER = {'Authorization': self.API_TOKEN,
                               'accept': 'application/json'}
        except KeyError:
            _logger.debug("set BITRISE_TOKEN")
            exit()

    def get_apps(self):
        resp = requests.get('https://api.bitrise.io/v0.1/apps',
                            headers=self.API_HEADER)
        if resp.status_code != 200:
            raise _logger.error('GET /apps/ {}'.format(resp.status_code))
        return resp.json()

    def set_app(self, project, apps):
        if apps is not None:
            if project == "android":
                self.APP_SLUG = apps['data'][0]['slug']
            elif project == "ios":
                self.APP_SLUG = apps['data'][1]['slug']

    def get_app(self, project, apps):
        if not self.APP_SLUG:
            resp = requests.get('https://api.bitrise.io/v0.1/apps/{0}'.
                                format(self.APP_SLUG),
                                headers=self.API_HEADER)
            if resp.status_code != 200:
                raise _logger.error('GET /apps/ {}'.format(resp.status_code))
            return resp.json()

    def get_workflows(self, APP_SLUG):
        resp = \
            requests.get('https://api.bitrise.io/v0.1/apps/{0}'
                         '/build-workflows'.format(self.APP_SLUG),
                         headers=self.API_HEADER)
        if resp.status_code != 200:
            raise _logger.error('GET /apps/ {}'.format(resp.status_code))
        return resp.json()

    def get_builds(self):
        resp = \
            requests.get('https://api.bitrise.io/v0.1/apps/{0}'
                         '/builds'.format(self.APP_SLUG),
                         headers=self.API_HEADER)
        if resp.status_code != 200:
            raise _logger.error('GET /apps/ {}'.format(resp.status_code))
        return resp.json()

    def get_failure_count(self, builds):
        failure_count = int()
        if type(builds) is dict:
            for build in builds['data']:
                if(build['status'] == Status.FAILURE.value):
                    failure_count += 1
        elif type(builds) is list:
            for build in builds:
                if(build['status'] == Status.FAILURE.value):
                    failure_count += 1
        return failure_count

    def get_success_count(self, builds):
        success_count = int()
        if type(builds) is dict:
            for build in builds['data']:
                if(build['status'] == Status.SUCCESSFUL.value):
                    success_count += 1
        elif type(builds) is list:
            for build in builds:
                if(build['status'] == Status.SUCCESSFUL.value):
                    success_count += 1
        return success_count

    def get_not_finished_count(self, builds):
        not_finished_count = int()
        if type(builds) is dict:
            for build in builds['data']:
                if(build['status'] == Status.NOT_FINISHED.value):
                    not_finished_count += 1
        elif type(builds) is list:
            for build in builds:
                if(build['status'] == Status.NOT_FINISHED.value):
                    not_finished_count += 1
        return not_finished_count

    def get_aborted_failure(self, builds):
        aborted_failure_count = int()
        if type(builds) is dict:
            for build in builds['data']:
                if(build['status'] == Status.ABORTED_FAILURE.value):
                    aborted_failure_count += 1
        elif type(builds) is list:
            for build in builds:
                if(build['status'] == Status.ABORTED_FAILURE.value):
                    aborted_failure_count += 1
        return aborted_failure_count

    def get_aborted_success(self, builds):
        aborted_success = int()
        if type(builds) is dict:
            for build in builds['data']:
                if(build['status'] == Status.ABORTED_SUCCESS.value):
                    aborted_success += 1
        elif type(builds) is list:
            for build in builds:
                if(build['status'] == Status.ABORTED_SUCCESS.value):
                    aborted_success += 1
        return aborted_success

    def get_builds_for_workflow(self, builds, workflow):
        builds_for_workflow = []
        for build in builds['data']:
            if(build['triggered_workflow'] == workflow):
                builds_for_workflow.append(build)
        return builds_for_workflow


def main():
    args = parse_args(sys.argv[1:])
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    b = Bitrise()
    all_apps = b.get_apps()

    b.set_app(args.project, all_apps)
    workflows = b.get_workflows(b.APP_SLUG)

    builds = b.get_builds()
    failures = b.get_failure_count(builds)
    print("All recent builds Failure count: {0}".format(failures))

    successes = b.get_success_count(builds)
    print("All recent builds Success count: {0}".format(successes))

    not_finished = b.get_not_finished_count(builds)
    print("All recent builds Not finished count: {0}".format(not_finished))

    aborted_failure = b.get_aborted_failure(builds)
    print("Aborted failure count: {0}".format(aborted_failure))

    aborted_success = b.get_aborted_success(builds)
    print("Aborted success count: {0}".format(aborted_success))

    builds = b.get_builds_for_workflow(
        builds, Workflows.NEW_XCODE.value)

    failures = b.get_failure_count(builds)
    print("Failure count for workflow: {0}".format(failures))

    successes = b.get_success_count(builds)
    print("Success count for workflow: {0}".format(successes))

    not_finished = b.get_not_finished_count(builds)
    print("No finished count: {0}".format(not_finished))

    print(*workflows['data'], sep=", ")


if __name__ == '__main__':
    main()
