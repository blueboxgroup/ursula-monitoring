#!/usr/bin/env python


# This plugin gives information about the hypervisors. It works as is if using Python2.7 but to get it working with Python2.6 and
# before (as well as Python 3.0) require that you number the placeholders in the format method().
# This way wherever the {} is used, number it starting from 0. e.g., {0}.nova.hypervisor

# #RED
from argparse import ArgumentParser
import socket
import time
import os

import shade

DEFAULT_SCHEME = '{}.nova.hypervisors'.format(socket.gethostname())

METRIC_KEYS = (
    'current_workload',
    'disk_available_least',
    'local_gb',
    'local_gb_used',
    'memory_mb',
    'memory_mb_used',
    'running_vms',
    'vcpus',
    'vcpus_used',
)

def output_metric(name, value):
    print '{}\t{}\t{}'.format(name, value, int(time.time()))

def main():
    parser = ArgumentParser()
    parser.add_argument('-H', '--host')
    parser.add_argument('-s', '--scheme', default=DEFAULT_SCHEME)
    args = parser.parse_args()

    cloud = shade.openstack_cloud()
	
    if args.host:
        hypervisors = cloud.nova_client.hypervisors.search(args.host)
    else:
        hypervisors = cloud.nova_client.hypervisors.list()

    for hv in hypervisors:
        hostname = hv.hypervisor_hostname.split('.')[0]
        for key, value in hv.to_dict().iteritems():
            if key in METRIC_KEYS:
                output_metric('{}.{}.{}'.format(args.scheme, hostname, key), value)

if __name__ == '__main__':
    main()
