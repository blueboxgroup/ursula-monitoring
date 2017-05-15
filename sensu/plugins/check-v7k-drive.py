#!/usr/bin/env python

#   Author: Bing Hu
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations

import argparse
import os
import re
import subprocess
import sys

CHECK = "canister-disk check"
SUCCESS = 'success'
CRITICAL = 'critical'
WARNING = 'warning'

RETURN_STATUS = {
    SUCCESS: 0,
    CRITICAL: 2,
    WARNING: 1,
}
DEFAULT_FAILED_RETURN = CRITICAL


def exit_with_status(status):
    return_status = RETURN_STATUS[status]
    sys.exit(return_status)


def ssh_key_exists(path):
    return os.path.exists(path)


def get_mdisks(args):
    if not ssh_key_exists(args.ssh_key):
        print("%s CRITICAL:private key no present at %s" %
              (CHECK, args.ssh_key))
        exit_with_status(WARNING)

    cmd = "ssh -i %s -p %s %s@%s  lsmdisk -filtervalue mdisk_grp_name=%s|awk '{print $2}'" % (
        args.ssh_key, args.v7k_port, args.user, args.v7k_host, args.pool_name)
    output = subprocess.check_output(cmd, shell=True)
    firstrow = True
    mdisks = list()
    for mdisk in output.split('\n'):
        if firstrow:
            firstrow = False
            continue
        if mdisk:
            mdisks.append(mdisk)
    return mdisks


def check_v7k_disk(args):
    mdisks=get_mdisks(args)
    for mdisk in mdisks:
        cmd = "ssh -i %s -p %s %s@%s lsdrive -filtervalue mdisk_name=%s|awk '{print $1 \"\t\"  $2}'" % (
            args.ssh_key, args.v7k_port, args.user, args.v7k_host,mdisk)
        output = subprocess.check_output(cmd, shell=True)
        firstrow = True
        for line in output.split('\n'):
            if firstrow:
                firstrow = False
                continue
            node_info = line.split()
            if len(node_info) >= 2:
                disk = line.split()[0]
                status = line.split()[1]
            else:
                continue
            if status != 'online':
                print('%s CRITICAL:Disk(%s) is under %s status' %
                      (CHECK, disk, status))
                exit_with_status(CRITICAL)
    print('%s OK:All disks are online' % (CHECK))
    exit_with_status(SUCCESS)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--v7k-host',
                        help="management ip address for v7k")

    parser.add_argument('-p', '--v7k-port',
                        help="ssh port for v7k")

    parser.add_argument('-u', '--user',
                        help="user to access v7k ")

    parser.add_argument('-i', '--ssh-key',
                        help="private key to access v7k")

    parser.add_argument('-n', '--pool-name',
                        help="v7k pool name")

    parser.add_argument('--criticality', '-z',
                        help='Set sensu alert level, critical is default',
                        default='critical')
    args = parser.parse_args()
    try:
        check_v7k_disk(args)
    except Exception as e:
        print("'%s CRITICAL:Failed to check v7k disk status: %s" % (CHECK, e))
        exit_with_status(CRITICAL)
    exit_with_status(SUCCESS)


if __name__ == '__main__':
    main()
