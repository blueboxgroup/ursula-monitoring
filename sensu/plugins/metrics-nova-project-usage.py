#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import time
import argparse
import traceback
from datetime import datetime, timedelta

import shade
import novaclient

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


class CloudMetrics(object):
    def __init__(self):
        self.cloud = shade.openstack_cloud()

    def get_projects(self):
        return (project['id'] for project in self.cloud.list_projects())

    def get_usage(self, project_ids, minutes, hours, days):
        stop = datetime.now()
        start = stop - timedelta(minutes=minutes, hours=hours, days=days)
        for id_ in project_ids:
            usage = (
                self.cloud.nova_client.usage.get(id_, start, stop).to_dict())
            usage['id'] = id_
            yield usage

    def graphite_print(self, usage):
        utime = time.time()
        metric_path = "usage.nova.project_id.{id}.{name}"
        outstr = "{metric_path} {value} {time}"

        for usg in usage:
            id_ = usg['id']
            for key, val in usg.items():
                if key in ['id', 'start', 'stop', 'server_usages']:
                    continue
                path = metric_path.format(id=id_, name=key)
                print(outstr.format(metric_path=path, value=val, time=utime))

    def run(self, args):
        projects = self.get_projects()
        try:
            usage = self.get_usage(
                projects, args.minutes, args.hours, args.days
            )
        except novaclient.exceptions.Forbidden:
            traceback.print_exc()
            print('Ensure the stackrc is configured for an admin '
                  'user.', file=sys.stderr)
            sys.exit(CRITICAL)
        self.graphite_print(usage)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--days',
        type=int,
        default=0,
        help="usage starting x days ago (Default: 0)"
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=1,
        help="usage starting x hours ago (Default: 1)"
    )
    parser.add_argument(
        '--minutes',
        type=int,
        default=0,
        help="usage starting x minutes ago (Default: 0)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    CloudMetrics().run(args)


if __name__ == '__main__':
    main()
