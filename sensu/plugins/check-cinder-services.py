#!/usr/bin/env python
#
# Check OpenStack Cinder Service Status
# ===
#
# Dependencies
# -----------
# - shade libraries
#
# Performs query to determine 'alive' status of all
# cinder service. 
#
# Copyright 2017 Xiaohua Shen <shenxh@cn.ibm.com>
#
# Released under the same terms as Sensu (the MIT license);
# see LICENSE for details.
#

import shade
import argparse
import sys

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

# get options
argparser = argparse.ArgumentParser()
argparser.add_argument('--criticality', '-z',
                       help='Set sensu alert level, critical is default',
                       default='critical')
options = argparser.parse_args()

# set alert level
if options.criticality == 'critical':
    exit_alert_state = STATE_CRITICAL
else:
    exit_alert_state = STATE_WARNING

# get cinder service list with down state
cloud = shade.openstack_cloud()
cinder = cloud.cinder_client

services_down=[]
for service in cinder.services.list():
    if service.state == 'down':
        services_down.append(service)

if len(services_down) > 0:
    print "Alert: %d Cinder service(s) down" %len(services_down)
    print services_down
    sys.exit(exit_alert_state)
else:
    print "OK: No Cinder service(s) down"
    sys.exit(STATE_OK)