#!/usr/bin/env python
#
# Checks CPU usage
#
# Return WARNING if CPU usage is over warning value, default 80%
# Return CRITICAL if CPU usage is over critical value, default 95%
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', '--ip', help='vyatta vrrp ip',
                        required=True)
    parser.add_argument('-p', '--password', help='snmp password',
                        required=True)
    parser.add_argument('-w', '--warning',
                        help='percent cpu usage to throw warning',
                        required=False, default=80)
    parser.add_argument('-c', '--critical',
                        help='percent cpu usage to throw critical error',
                        required=False, default=95)
    args = parser.parse_args()

    cmd = "snmpget -u sensu -A %s -a md5 -l authNoPriv %s \
           1.3.6.1.4.1.2021.11.11.0" % (args.password, args.ip)

    try:
        snmp_output = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        print('CRITICAL: Failed to retrieve Vyatta CPU usage via SNMP')
        sys.exit(STATE_CRITICAL)

    cpu_idle = int(snmp_output.split("INTEGER: ")[1].rstrip())
    cpu_usage = 100 - cpu_idle

    if cpu_usage > args.critical:
        print("CRITICAL: Vyatta CPU usage: %d%%" % cpu_usage)
        sys.exit(STATE_CRITICAL)
    elif cpu_usage > args.warning:
        print("WARNING: Vyatta CPU usage: %d%%" % cpu_usage)
        sys.exit(STATE_WARNING)
    else:
        print("OK: Vyatta CPU usage: %d%%" % cpu_usage)
        sys.exit(STATE_OK)

if __name__ == "__main__":
    main()
