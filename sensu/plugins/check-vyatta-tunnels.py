#!/usr/bin/env python
#
# Checks that all tunnels are up
#
# Return CRITICAL if any tunnel is down
#
# Dean Daskalantonakis <ddaskal@us.ibm.com>
# Carl Hannusch <channusch@us.ibm.com>

import argparse
import re
import subprocess
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
    parser.add_argument('-ip', '--ip', help='vyatta vrrp ip',
                        required=True)
    parser.add_argument('-p', '--password', help='snmp password',
                        required=True)
    parser.add_argument('-z', '--criticality', help='check criticality',
                        default='critical')
    args = parser.parse_args()

    CRITICALITY = args.criticality

    status = ""
    cmd = "snmpwalk -u sensu -A %s -a md5 -l authNoPriv %s \
           1.3.6.1.2.1.2.2.1.2" % (args.password, args.ip)
    try:
        device_list = subprocess.check_output(cmd, shell=True).split("\n")
    except subprocess.CalledProcessError as e:
        print(e.output)
        print('%s: Failed to retrieve Vyatta devices \
                name via SNMP' % args.criticality.upper())
        switch_on_criticality()

    cmd = "snmpwalk -u sensu -A %s -a md5 -l authNoPriv %s \
           1.3.6.1.2.1.2.2.1.8" % (args.password, args.ip)
    try:
        device_status = subprocess.check_output(cmd, shell=True).split("\n")
    except subprocess.CalledProcessError as e:
        print(e.output)
        print('%s: Failed to retrieve Vyatta device states \
                status via SNMP' % args.criticality.upper())
        switch_on_criticality()

    for index, device in enumerate(device_list):
        if " vti" in str(device):
            status += "Device: %s " % device.split("STRING: ")[1].rstrip()
            status += "%s\n" % device_status[index].split("INTEGER: ")[1]

    if "down" in status:
        print("%s: One or more tunnels are down on Vyatta:\n%s"
              % (args.criticality.upper(), status))
        switch_on_criticality()
    else:
        print("OK: All tunnels are up on Vyatta:\n%s" % status)
        sys.exit(STATE_OK)

if __name__ == "__main__":
    main()
