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

CHECK = "canister-status check"
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


def check_canister_status(args):
    if not ssh_key_exists(args.ssh_key):
        print("%s CRITICAL:private key no present at %s" %
              (CHECK, args.ssh_key))
        exit_with_status(WARNING)

    cmd = "ssh -i %s -p %s %s@%s lsnodecanister|awk '{print $2 \"\t\"  $4}'" % (
        args.ssh_key, args.v7k_port, args.user, args.v7k_host)
    output = subprocess.check_output(cmd, shell=True)
    for line in output.split('\n'):
        match = re.match('offline', line)
        if match:
            print('%s CRITICAL:Canister(%s) is offline' %
                  (CHECK, line.split()[0]))
            exit_with_status(CRITICAL)
    print('%s OK:Both Canisters are online' % (CHECK))
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

    parser.add_argument('--criticality', '-z',
                        help='Set sensu alert level, critical is default',
                        default='critical')
    args = parser.parse_args()
    try:
        check_canister_status(args)
    except Exception as e:
        print("'%s CRITICAL:Failed to check v7k status: %s" % (CHECK, e))
        exit_with_status(CRITICAL)
    exit_with_status(SUCCESS)


if __name__ == '__main__':
    main()
