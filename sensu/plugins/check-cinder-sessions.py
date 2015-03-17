#!/usr/bin/python
#
# Copyright 2015, Craig Tracey <craigtracey@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import subprocess
import sys

from novaclient.v1_1.client import Client as nova_client

CREDS = {
    'username': os.environ['OS_USERNAME'],
    'api_key': os.environ['OS_PASSWORD'],
    'project_id': os.environ['OS_TENANT_NAME'],
    'auth_url': os.environ['OS_AUTH_URL'],
    'region_name': 'RegionOne',
}


def _get_hostname():
    return subprocess.check_output(['hostname', '-f']).strip()


def _get_local_active_instance_volumes():
    hostname = _get_hostname()

    local_attached_vols = []
    nova = nova_client(**CREDS)
    search_opts = {
        'all_tenants': True
    }
    for server in nova.servers.list(search_opts=search_opts):
        if getattr(server, "OS-EXT-STS:vm_state") != "active":
            continue
        server_hv = \
            getattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname')
        attached_vols = \
            getattr(server, 'os-extended-volumes:volumes_attached')
        if server_hv == hostname and len(attached_vols):
            local_attached_vols += attached_vols
    return local_attached_vols


def _get_active_iscsi_volumes():
    volumes = set()
    out = subprocess.check_output(['iscsiadm', '-m', 'session'])
    for line in out.strip().split('\n'):
        parts = line.split(':')
        volumes.add(parts[-1][7:])  # remove 'volume-'
    return list(volumes)


def main():
    failure = False
    try:
        expected_vols = _get_local_active_instance_volumes()
        connected_vols = _get_active_iscsi_volumes()

        for vol in expected_vols:
            if not vol['id'] in connected_vols:
                print "Volume %s is 'in-use' but not " \
                      "connected" % vol['id']
                failure = True
    except Exception as e:
        print "Could not run check: %s" % e
        sys.exit(2)
    sys.exit(failure)


if __name__ == '__main__':
    main()
