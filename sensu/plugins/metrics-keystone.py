#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import time
import traceback
from collections import namedtuple
from argparse import ArgumentParser

import shade

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3
V2_ERR_MSG = 'This script assumes it runs with v2 auth and a v2 keystone ' \
             'client. Please use a v2 stackrc or complain very loudly.'


class CloudMetrics(object):
    def __init__(self, scheme):
        self.cloud = shade.openstack_cloud()
        self._projects = None
        self._users = None
        self._scheme = scheme

    @property
    def projects(self):
        if self._projects is None:
            try:
                self._projects = self.cloud.keystone_client.tenants.list()
            except AttributeError:
                # Why AttributeError?  Because the calls that I make to the
                # internal client will thrown an attribute error if it doesn't
                # have 'tenants'. This is due to the v3 API, and I'm not
                # planning on that ATM.
                traceback.print_exc()
                print(V2_ERR_MSG, file=sys.stderr)
                sys.exit(CRITICAL)
        return self._projects

    @property
    def users(self):
        if self._users is None:
            self._users = self.cloud.list_users()
        return self._users

    def num_projects(self):
        return len(self.projects)

    def num_users(self):
        return len(self.users)

    def users_per_project(self):
        UsersPerProject = namedtuple('UsersPerProject', 'proj_name, num_users')
        return (UsersPerProject(proj.name, len(proj.list_users()))
                for proj in self.projects)

    def graphite_print(self, users, projects, users_per_proj):
        utime = time.time()
        metric_path = "usage.keystone.{path}"
        if self._scheme:
            metric_path = self._scheme + "."+ metric_path 
        outstr = "{metric_path} {value} {time}"

        path = metric_path.format(path='users')
        print(outstr.format(metric_path=path, value=users, time=utime))

        path = metric_path.format(path='projects')
        print(outstr.format(metric_path=path, value=projects, time=utime))

        for proj in users_per_proj:
            p = 'project_name.{}.users'.format(proj.proj_name)
            path = metric_path.format(path=p)
            print(outstr.format(
                metric_path=path, value=proj.num_users, time=utime
            ))

    def run(self):
        users = self.num_users()
        projects = self.num_projects()
        users_per_project = self.users_per_project()
        self.graphite_print(users, projects, users_per_project)


def main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--scheme')
    args = parser.parse_args()
    try:
        CloudMetrics(args.scheme).run()
    except shade.exc.OpenStackCloudException:
        traceback.print_exc()
        print(V2_ERR_MSG, file=sys.stderr)
        sys.exit(CRITICAL)


if __name__ == '__main__':
    main()
