#!/usr/bin/env python
#
# Calls neutron agent api
# Checks for routers that have multiple active or all down l3 agents
#
# return CRITICAL if any routers found with more than one active l3 agent
# return CRITICAL if any routers found with all l3 agents standby
#
# Dean Daskalantonakis <ddaskal@us.ibm.com>

import argparse
import sys
import os

import shade

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2


def check_router(router, router_agents):
    # Inputs: router dict & all agents associated with the router
    # Outputs: STATE_CRITICAL if any bad agents were found
    #          STATE_WARNING if no HA state found for l3 agent
    #          STATE_OK if one and only one active agent
    # Checks each agent for one active & rest standby status
    # This is called once per router

    active_agent = False

    for agent in router_agents['agents']:
        if 'ha_state' not in agent.keys():
            print("WARNING: No HA state for l3 agent %s" % agent['id'])
            return STATE_WARNING
        if active_agent and agent['ha_state'] == 'active':
            print("ERROR: Multiple active l3 agents on router %s"
                  % router['id'])
            return STATE_CRITICAL
        if agent['ha_state'] == 'active':
            active_agent = True

    if not active_agent:
        print("ERROR: No active l3 agents for router %s" % router['id'])
        return STATE_CRITICAL

    return STATE_OK


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--max_routers', type=int, default=100)
    args = parser.parse_args()
    agent_status = STATE_OK

    search_opts = {
        'all_tenants': True,
        }
		
    cloud = shade.openstack_cloud()
    neutron = cloud.neutron_client
    router_list = neutron.list_routers()
    if len(router_list['routers']) > args.max_routers:
        print("WARNING: Number of routers more than the max: %d"
              % args.max_routers)
        sys.exit(STATE_WARNING)

    for router in router_list['routers']:
        search_opts['router'] = router['id']
        router_agents = neutron.list_l3_agent_hosting_routers(**search_opts)
        agent_status = check_router(router, router_agents)
        if agent_status == STATE_CRITICAL:
            sys.exit(STATE_CRITICAL)
        elif agent_status == STATE_WARNING:
            sys.exit(STATE_WARNING)

    if agent_status == STATE_OK:
        print("OK: No routers with multiple active or all inactive l3 agents")
        sys.exit(STATE_OK)


if __name__ == "__main__":
    main()
