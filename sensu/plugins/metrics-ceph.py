# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import time
import argparse
import traceback

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

try:
    import rados
except ImportError:
    traceback.print_exc()
    print('This check assumes it runs on a ceph instance with python-rados '
          'installed; please insure this instance is a ceph-osd node with '
          'python-rados installed.', file=sys.stderr)
    sys.exit(CRITICAL)


class MetricsCheck(object):
    def __init__(self, ceph_keyring, ceph_conf):
        self.keyring = ceph_keyring
        self.conf = ceph_conf
        self.cluster = None
        self.setup_ceph()

    def setup_ceph(self):
        self.cluster = rados.Rados(
            conffile=self.conf,
            conf={
                'keyring': self.keyring
            }
        )
        self.cluster.connect()

    def graphite_print(self, pools, cluster):
        utime = time.time()
        pool_metric_path = "usage.ceph.pool.{pool}.{key}"
        cluster_metric_path = "usage.ceph.cluster.{key}"
        outstr = "{metric_path} {value} {time}"

        for key, val in cluster.items():
            path = cluster_metric_path.format(key=key)
            print(outstr.format(metric_path=path, value=val, time=utime))

        for pool, data in pools:
            for key, val in data.items():
                path = pool_metric_path.format(pool=pool, key=key)
                print(outstr.format(metric_path=path, value=val, time=utime))

    def get_cluster_data(self):
        return self.cluster.get_cluster_stats()

    def get_pool_data(self):
        pools = self.cluster.list_pools()
        results = []
        for pool in pools:
            ioctx = self.cluster.open_ioctx(pool)
            results.append([pool, ioctx.get_stats()])
        return results

    def run(self):
        pools = self.get_pool_data()
        cluster = self.get_cluster_data()
        self.graphite_print(pools, cluster)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--ceph-keyring',
        metavar='/etc/ceph/ceph.client.admin.keyring',
        default='/etc/ceph/ceph.client.admin.keyring',
        help='Ceph client keyring file'
    )
    parser.add_argument(
        '--ceph-conf',
        metavar='/etc/ceph/ceph.conf',
        default='/etc/ceph/ceph.conf',
        help='Ceph client conf file'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    chk = MetricsCheck(args.ceph_keyring, args.ceph_conf)
    chk.run()


if __name__ == '__main__':
    main()
