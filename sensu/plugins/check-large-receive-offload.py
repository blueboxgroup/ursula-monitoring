#!/usr/bin/env python
#
# Checks that large receive offload is disabled
#
# Return CRITICAL if large receive offload is enabled
#
# Dean Daskalantonakis <ddaskal@us.ibm.com>

import argparse
import re
import subprocess
import sys

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2


def exit_with_error_status(warning):
    if warning:
        sys.exit(STATE_WARNING)
    else:
        sys.exit(STATE_CRITICAL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--interface', help='primary interface')
    parser.add_argument('-w', '--warning', action='store_true')
    args = parser.parse_args()

    crit_level = 'CRITICAL'
    if args.warning:
        crit_level = 'WARNING'

    if args.interface is None:
        parser.print_help()
        exit_with_error_status(args.warning)

    devices = re.findall('eth[0-7]', args.interface)

    for eth in devices:
        cmd = "ethtool -k %s | grep large-receive-offload | \
               grep ' off'" % (eth)

        lro_check = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        stdout, stderr = lro_check.communicate()

        if lro_check.returncode != 0:
            print('%s: Device %s has large-receive-offload (LRO) enabled'
                  % (crit_level, eth))
            exit_with_error_status(args.warning)
        else:
            print('Device %s has large-receive-offload (LRO) disabled' % (eth))

    sys.exit(STATE_OK)

if __name__ == "__main__":
    main()
