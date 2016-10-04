#!/usr/bin/env python
#
# Checks that all interfaces are enabled
#
# Return CRITICAL if any interface is disabled
#
# Dean Daskalantonakis <ddaskal@us.ibm.com>
# Carl Hannusch <channusch@us.ibm.com>

import argparse
import re
import subprocess
import sys

STATE_OK = 0
STATE_CRITICAL = 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', '--ip', help='vyatta vrrp ip',
                        required=True)
    parser.add_argument('-p', '--password', help='snmp password',
                        required=True)
    args = parser.parse_args()

    status = ""
    cmd = "snmpwalk -u sensu -A %s -a md5 -l authNoPriv %s \
           1.3.6.1.2.1.2.2.1.2" % (args.password, args.ip)
    try:
        device_list = subprocess.check_output(cmd, shell=True).split("\n")
    except subprocess.CalledProcessError as e:
        print(e.output)
        print('CRITICAL: Failed to retrieve Vyatta ethernet device \
                name via SNMP')
        sys.exit(STATE_CRITICAL)

    cmd = "snmpwalk -u sensu -A %s -a md5 -l authNoPriv %s \
           1.3.6.1.2.1.2.2.1.8" % (args.password, args.ip)
    try:
        device_status = subprocess.check_output(cmd, shell=True).split("\n")
    except subprocess.CalledProcessError as e:
        print(e.output)
        print('CRITICAL: Failed to retrieve Vyatta ethernet device \
                status via SNMP')
        sys.exit(STATE_CRITICAL)

    for index, device in enumerate(device_list):
        if "bond" in str(device):
            if "bond0v1" in str(device) or "bond1v1" in str(device):
                continue
            status += "Device: %s " % device.split("STRING: ")[1].rstrip()
            status += "%s\n" % device_status[index].split("INTEGER: ")[1]

    if "down" in status:
        print("CRITICAL: One or more bonded interfaces are down on Vyatta:\n%s"
              % status)
        sys.exit(STATE_CRITICAL)
    else:
        print("OK: All bonded interfaces are up on Vyatta:\n%s" % status)
        sys.exit(STATE_OK)

if __name__ == "__main__":
    main()
