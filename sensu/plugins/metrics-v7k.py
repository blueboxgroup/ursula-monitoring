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
import subprocess
import time

DEFAULT_SCHEME = 'v7k.{}.{}'


def ssh_key_exists(path):
    return os.path.exists(path)


def metric_output(args):
    if not ssh_key_exists(args.ssh_key):
        print("private key no present at %s" % args.ssh_key)

    cmd = "ssh -i %s  -p %s  %s@%s lsnodecanisterstats" % (
        args.ssh_key, args.v7k_port, args.user, args.v7k_host)
    output = subprocess.check_output(cmd, shell=True)
    firstrow = True
    for line in output.split('\n'):
        if firstrow:
            firstrow = False
            continue
        if not line:
            continue
        fields = line.split()
        if not fields:
            continue
        print '{}.{}.{}\t{}\t{}'.format(args.scheme,
                                        fields[1],
                                        fields[2],
                                        fields[3],
                                        int(time.time()))


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

    parser.add_argument('-s', '--scheme', default=DEFAULT_SCHEME)

    args = parser.parse_args()
    metric_output(args)

if __name__ == '__main__':
    main()
