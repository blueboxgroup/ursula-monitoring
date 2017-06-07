#!/usr/bin/env python
#
# Checks if ILMT LockState is true
#
# Craig Tracey <cmt@us.ibm.com>
# Xiaohua Shen <shenxh@cn.ibm.com>

import argparse
import os
import sys
import ConfigParser

from distutils.util import strtobool

DEFAULT_ILMT_CONFIG = "/var/opt/BESClient/besclient.config"
ILMT_CONFIG_LOCK_SECTION = "Software\BigFix\EnterpriseClient\Settings\Client\__LockState"  # noqa

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2

def check_ilmt_locked(filename):
    try:
        if not os.path.isfile(filename):
            raise Exception("Config file does not exist: %s" % filename)

        config = ConfigParser.ConfigParser()
        config.read(filename)
        ilmt_locked = config.get(ILMT_CONFIG_LOCK_SECTION, 'value')
        return bool(strtobool(ilmt_locked))
    except Exception as e:
        print >> sys.stderr, "ILMT locked check failed with error: %s" % e
        sys.exit(STATE_CRITICAL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ilmt-config', '-f', default=DEFAULT_ILMT_CONFIG)
    parser.add_argument('--criticality', '-z',
                            help='Set sensu alert level, critical is default',
                            default='critical')
    args = parser.parse_args()

    rc = check_ilmt_locked(args.ilmt_config)
    if rc:
        print("OK: ILMT LockState is true")
        sys.exit(STATE_OK)

    if args.criticality == 'critical':
        print("CRITICAL: ILMT LockState is false")
        sys.exit(STATE_CRITICAL)
    else:
        print("WARNING: ILMT LockState is false")
        sys.exit(STATE_WARNING)


if __name__ == '__main__':
    main()
