# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import time
import traceback

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

    def get_quotas(self, project_ids):
        return (self.cloud.nova_client.quotas.get(id_)._info.copy()
                for id_ in project_ids)

    def graphite_print(self, quotas):
        utime = time.time()
        metric_path = "quotas.nova.project_id.{id}.{name}"
        outstr = "{metric_path} {value} {time}"

        for quota in quotas:
            id_ = quota['id']
            for key, val in quota.items():
                if key == 'id':
                    continue
                path = metric_path.format(id=id_, name=key)
                print(outstr.format(metric_path=path, value=val, time=utime))

    def run(self):
        projects = self.get_projects()
        try:
            quotas = self.get_quotas(projects)
        except novaclient.exceptions.Forbidden:
            traceback.print_exc()
            print('Ensure the stackrc is configured for an admin '
                  'user.', file=sys.stderr)
            sys.exit(CRITICAL)
        self.graphite_print(quotas)


def main():
    CloudMetrics().run()


if __name__ == '__main__':
    main()
