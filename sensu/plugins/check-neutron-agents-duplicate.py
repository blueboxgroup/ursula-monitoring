#!/usr/bin/env python
#
# Calls neutron agent api
# Checks that there are no duplicate neutron agents with the same hostname
# return CRITICAL if any duplicate agents
# return OK if no duplicate agents
#
# Jose L Coello Enriquez <jlcoello@us.ibm.com>
# Dean Daskalantonakis <ddaskal@us.ibm.com>
# Rachel Wong <rcwong@.us.ibm.com>

import argparse
import sys
import os

from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.v2_0 import client as neutron_client

username = os.environ['OS_USERNAME']
password = os.environ['OS_PASSWORD']
project_name = os.environ['OS_TENANT_NAME']
auth_url = os.environ['OS_AUTH_URL']
user_domain_name = os.getenv('OS_USER_DOMAIN_NAME', 'Default')
project_domain_name = os.getenv('OS_PROJECT_DOMAIN_NAME', 'Default')

auth = identity.Password(username=username,
                         password=password,
                         project_name=project_name,
                         auth_url=auth_url,
                         user_domain_name=user_domain_name,
                         project_domain_name=project_domain_name)

sess = session.Session(auth=auth)
neutron = neutron_client.Client(session=sess)

STATE_OK = 0
STATE_CRITICAL = 1

def check_agents(agent_list):
    agent_dictionary = {}

    for agent in agent_list['agents']:
        agent_type = agent['agent_type']
        host = agent['host']

        if agent_type in agent_dictionary:
            if host in agent_dictionary[agent_type]:
                print("Duplicate agent: %s on host: %s" % (agent_type, host))
		return STATE_CRITICAL
            else:
                agent_dictionary[agent_type].add(host)
        else:
            agent_dictionary[agent_type] = set()
            agent_dictionary[agent_type].add(host)

    return STATE_OK

def main():
    agent_status = STATE_OK
    agent_list = neutron.list_agents()

    agent_status = check_agents(agent_list)
    if agent_status == STATE_CRITICAL:
        print ("CRITICAL: Duplicate neutron agents.")
	sys.exit(STATE_CRITICAL)
    elif agent_status == STATE_OK:
	print ("OK: No duplicate neutron agents.")
	sys.exit(STATE_OK)
    
if __name__ == "__main__":
    main()
