#!/usr/bin/env python
#
# Checks VRRP Status of Vyattas
#
# Return CRITICAL if there is not one and only one MASTER
# or if there is any state other than BACKUP/MASTER present
#
# Dean Daskalantonakis <ddaskal@us.ibm.com>
# Carl Hannusch <channusch@us.ibm.com>

import argparse
import re
import subprocess
import sys

STATE_OK = 0
STATE_CRITICAL = 2

INIT = 0
BACKUP = 1
MASTER = 2
FAULT = 3
UNKNOWN = 4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--primary', help='primary vyatta ip',
                        required=True)
    parser.add_argument('-s', '--secondary', help='secondary vyatta ip',
                        required=True)
    parser.add_argument('-pass', '--password', help='snmp password',
                        required=True)
    args = parser.parse_args()

    cmd = "snmpget -u sensu -A %s -a md5 -l authNoPriv %s \
           1.3.6.1.4.1.9586.100.5.2.1.1.3.1" % (args.password, args.primary)
    try:
        snmp_output = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        print('CRITICAL: Failed to retrieve Vyatta VRRP state via SNMP')
        sys.exit(STATE_CRITICAL)

    primary_state = int(snmp_output.split("INTEGER: ")[1].rstrip())
    if (primary_state == INIT):
        print('CRITICAL: Primary Vyatta in state INIT')
        sys.exit(STATE_CRITICAL)
    elif (primary_state == FAULT):
        print('CRITICAL: Primary Vyatta in state FAULT')
        sys.exit(STATE_CRITICAL)
    elif (primary_state == UNKNOWN):
        print('CRITICAL: Primary Vyatta in state UNKNOWN')
        sys.exit(STATE_CRITICAL)

    cmd = "snmpget -u sensu -A %s -a md5 -l authNoPriv %s \
           1.3.6.1.4.1.9586.100.5.2.1.1.3.1" % (args.password, args.secondary)
    try:
        snmp_output = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        print('CRITICAL: Failed to retrieve Vyatta VRRP state via SNMP')
        sys.exit(STATE_CRITICAL)

    secondary_state = int(snmp_output.split("INTEGER: ")[1].rstrip())
    if (secondary_state == INIT):
        print('CRITICAL: Secondary Vyatta in state INIT')
        sys.exit(STATE_CRITICAL)
    elif (secondary_state == FAULT):
        print('CRITICAL: Secondary Vyatta in state FAULT')
        sys.exit(STATE_CRITICAL)
    elif (secondary_state == UNKNOWN):
        print('CRITICAL: Secondary Vyatta in state UNKNOWN')
        sys.exit(STATE_CRITICAL)

    if (primary_state == secondary_state):
        print('CRITICAL: Both Vyattas are in the same VRRP state')
        sys.exit(STATE_CRITICAL)
    else:
        print("OK: Vyatta VRRP state normal")
        sys.exit(STATE_OK)

if __name__ == "__main__":
    main()
