#!/usr/bin/env python
#
# Checks static route for specific subnet
#
# Return CRITICAL if no route found
#
# Jose L Coello Enriquez <jlcoello@us.ibm.com>

import subprocess
import argparse
import sys

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
CRITICALITY = 'critical'

def switch_on_criticality():
    if CRITICALITY == 'warning':
        sys.exit(STATE_WARNING)
    else:
        sys.exit(STATE_CRITICAL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--subnet', help='provide subnet ip')
    parser.add_argument('-g', '--gateway', help='provide gateway')
    parser.add_argument('-z', '--criticality', default='critical')
    args = parser.parse_args()

    CRITICALITY = args.criticality

    if args.subnet is None or args.gateway is None:
        parser.print_help()
        switch_on_criticality()

    cmd = "ip route show %s via %s | grep %s" % (args.subnet , args.gateway, args.subnet)

    subnet_check = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = subnet_check.communicate()

    if subnet_check.returncode != 0 :
        print('Gateway: %s not found for Subnet: %s' % (args.gateway , args.subnet))
        switch_on_criticality()

    else:
        print('Gateway: %s set for Subnet: %s' % (args.gateway , args.subnet))
        sys.exit(STATE_OK)

if __name__ == "__main__":
    main()
