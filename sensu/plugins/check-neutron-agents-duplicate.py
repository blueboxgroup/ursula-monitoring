#!/usr/bin/env python
#
# Calls neutron agent api, checks for duplicate with same hostname
#
# return CRITICAL if any duplicate agent on same host found
#
# Jose L Coello Enriquez <jlcoello@us.ibm.com>

import argparse
import sys
import os
import json
import requests

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
CRITICALITY = 'critical'

timeout = 30

def switch_on_criticality():
    if CRITICALITY == 'warning':
        sys.exit(STATE_WARNING)
    else:
        sys.exit(STATE_CRITICAL)

def request(url, method='GET', retries=2, **kwargs):
    r = None
    try:
        for i in range(retries + 1):
            if i > 0:
                time.sleep(2)
            r = requests.request(method, url, **kwargs)
            if r.status_code:
                break
    except requests.exceptions.RequestException as e:
        print("%s returned %s" % (url, e))

    return r.json()

def check_agents(agent_list):
    agent_dictionary = {}

    for agent in agent_list['agents']:
        agent_type = agent['agent_type']
        host = agent['host'].split('.')[0]

        if agent_type  in agent_dictionary :
            if host in agent_dictionary[agent_type] :
                print("Duplicate agent: %s on host: %s" % (agent_type, host))
                switch_on_criticality()
            else:
                agent_dictionary[agent_type].add(host)
        else:
            agent_dictionary[agent_type] = set()
            agent_dictionary[agent_type].add(host)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', default=os.environ['OS_USERNAME'])
    parser.add_argument('-p', '--password', default=os.environ['OS_PASSWORD'])
    parser.add_argument('-t', '--tenant', default=os.environ['OS_TENANT_NAME'])
    parser.add_argument('-a', '--auth-url', default=os.environ['OS_AUTH_URL'])
    parser.add_argument('-z', '--criticality', default='critical')
    args = parser.parse_args()

    CRITICALITY = args.criticality
    url = args.auth_url + '/tokens'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    data = json.dumps(
        {
            'auth': {
                'tenantName': args.tenant,
                'passwordCredentials': {
                    'username': args.user,
                    'password': args.password
                }
            }
        })

    r = request(url, 'POST', 4, data=data, headers=headers)
    token = None
    if r:
        access = r['access']
        token = access['token']['id']

    if not token:
        switch_on_criticality()

    endpoints = {}
    for service in access['serviceCatalog']:
        for endpoint in service['endpoints']:
            endpoints[service['name']] = endpoint.get('internalURL')

    headers = {'Accept': 'application/json', 'X-Auth-Project-Id': args.tenant,
               'X-Auth-Token': token}

    endpoint = endpoints['neutron'] + '/v2.0/agents.json'
    agent_list = request(endpoint, headers=headers )
    if not agent_list :
        print("API call failed")
        sys.exit(STATE_WARNING)
    check_agents(agent_list)
    print("No duplicate neutron agaents")
    sys.exit(STATE_OK)

if __name__ == "__main__":
    main()
