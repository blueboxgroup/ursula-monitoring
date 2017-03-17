#!/usr/bin/env python

# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import time
import traceback

import shade
from argparse import ArgumentParser
import socket

DEFAULT_SCHEME = '{}'.format(socket.gethostname())

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

class CloudMetrics(object):
    def __init__(self, scheme):
        self.cloud = shade.openstack_cloud()
        self._scheme = scheme

    def get_limits(self, service_type):
        if service_type == "nova":
            return ([self.cloud.nova_client.limits.get(tenant_id=project['id'])._info.copy(),project['name']]
                for project in self.cloud.list_projects())
        if service_type == "cinder":
            return ([self.cloud.cinder_client.limits.get(tenant_id=project['id'])._info.copy(),project['name']]
                for project in self.cloud.list_projects())

    def graphite_print(self, limits, service_type):
        utime = int(time.time())
        metric_path = self._scheme + ".limits.{service_type}.project_name.{project_name}.absolute.{used_or_max}.{limit_name}"
        outstr = "{metric_path} {value} {time}"

        for limit in limits:
            project_name = limit[1]
            for rate_or_absolute, limit_values in limit[0].items():
                if rate_or_absolute == "rate":
                    continue
                for limit_name, val in limit_values.items():
                    used_or_max = "used" if limit_name.startswith("total") else "max"
                    path = metric_path.format(service_type=service_type,
                                              project_name=project_name, 
                                              used_or_max=used_or_max,
                                              limit_name=limit_name)
                    print(outstr.format(metric_path=path, value=val, time=utime))

    def run(self, service_type):
        try:
            limits = self.get_limits(service_type)
        except novaclient.exceptions.Forbidden:
            traceback.print_exc()
            print('Ensure the stackrc is configured for an admin '
                  'user.', file=sys.stderr)
            sys.exit(CRITICAL)
        self.graphite_print(limits, service_type)


def main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--scheme', default=DEFAULT_SCHEME)
    parser.add_argument('-S', '--service_type', default="nova")
    args = parser.parse_args()

    CloudMetrics(args.scheme).run(args.service_type)

if __name__ == '__main__':
    main()
