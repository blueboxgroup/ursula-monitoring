#!/usr/bin/env python
#
# Makes http calls to the different components to gather metric data
#
# Output service metrics for time taken, HTTP status code and status(0=Fail, 1=OK)
# When failing on a dependency, dummy HTTP status codes (600 or 700) are used
#
#
# Jose L Coello Enriquez <jlcoello@us.ibm.com>

import argparse
import re
import sys
import time
import socket
import os
import json
import subprocess
import requests

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2



DEFAULT_SCHEME = socket.gethostname()

def print_metric(metric_data):
    for line in metric_data:
        print(line)

def ceph_metric(cmd, metric_data, scheme):

    ceph_health = subprocess.Popen( cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = ceph_health.communicate()

    if ceph_health.returncode != 0 :
        print('Ceph Health failed: %s' % stderr)
        sys.exit(STATE_WARNING)

    if ('HEALTH_OK' in stdout) or ('HEALTH_WARN' in stdout):
        metric_data.append('%s.status 1' % scheme )

    else:
        metric_data.append('%s.status 0' % scheme )

    return metric_data

def service_list_metric(json_data, metric_data, scheme):
    services = json_data
    services_count = {}
    status = 1

    for i in services :
        name = i['binary']
        state = i['state']
        if name not in services_count:
            services_count[name] = 0

        if name == 'nova-compute':
            if i['status'] == 'enabled':
                if state != 'up':
                    metric_data.append('%s.status 0' % scheme )
                    return metric_data

        if state == 'up':
            services_count[name] += 1

    for key in services_count:
        if (services_count[key] == 0):
            status = 0
            break

    metric_data.append('%s.status %s ' % (scheme, status))
    return metric_data


def request_token(url, method='GET', retries=2, **kwargs):
    r = None
    try:
        for i in range(retries + 1):
            if i > 0:
                time.sleep(2)
            r = requests.request(method, url, **kwargs)
            if r.status_code :
                break
    except requests.exceptions.RequestException as e:
        print("%s returned %s" % (url, e))

    return r

def request(metric_data, scheme, url, timestamp, method='GET', retries=2, **kwargs):

    start = time.time()
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

    if r is None:
        status = 0
        status_code = 600
        time_taken = -10
    elif r.status_code != 200:
        status = 0
        status_code = r.status_code
        time_taken = -5
    else:
        status = 1
        status_code = r.status_code
        time_taken = round(time.time() - start, 3)


    metric_data.append('%s.time %s %s' % (scheme, time_taken, timestamp))
    metric_data.append('%s.code %s %s' % (scheme, status_code, timestamp))
    metric_data.append('%s.status %s %s' % (scheme, status, timestamp))
    return (r, metric_data)

def main():
    timestamp = int(time.time())
    requests.packages.urllib3.disable_warnings()    

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', default=os.environ['OS_USERNAME'])
    parser.add_argument('-p', '--password', default=os.environ['OS_PASSWORD'])
    parser.add_argument('-t', '--tenant', default=os.environ['OS_TENANT_NAME'])
    parser.add_argument('-a', '--auth-url', default=os.environ['OS_AUTH_URL'])
    parser.add_argument('-S', '--service-type', default='nova',
                        help='Service type must be provided')
    parser.add_argument('-s', '--scheme', default=DEFAULT_SCHEME)
    parser.add_argument('-f', '--fqdn', default=None,
                        help='fqdn must be provided for horizon')
    args = parser.parse_args()

    metric_data = []

    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(STATE_WARNING)

    scheme = ''
    if args.scheme == DEFAULT_SCHEME :
        scheme = args.scheme + '.' + args.service_type + '.api'
    else:
        scheme = args.scheme + '.' + args.service_type

    if args.service_type == 'ceph' :
        metric_data = ceph_metric('ceph health', metric_data, scheme)
        print_metric(metric_data)
        sys.exit(STATE_OK)

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


    if args.service_type == 'horizon':
        url = args.fqdn
        r, metric_data = request(metric_data, scheme, url,
                                 timestamp, headers=headers )
        print_metric(metric_data)
        sys.exit(STATE_OK)

    r = request_token(url, 'POST', 4, data=data, headers=headers)
    token = None
    if r:
        access = r.json()['access']
        token = access['token']['id']

    if not token:
        metric_data.append('%s.code %s %s' % (scheme, 700, timestamp))
        metric_data.append('%s.status %s %s' % (scheme, 0, timestamp))
        print_metric(metric_data)
        sys.exit(STATE_OK)

    tenant_id = access['token']['tenant']['id']

    endpoints = {}
    for service in access['serviceCatalog']:
        for endpoint in service['endpoints']:
            endpoints[service['name']] = endpoint.get('internalURL')

    headers = {'Accept': 'application/json', 'X-Auth-Project-Id': args.tenant,
               'X-Auth-Token': token}

    urls = {
        'keystone':('keystone', 'keystone' , '/tenants'),
        'nova':('nova', 'nova' , '/servers/detail'),
        'neutron':('neutron', 'neutron' ,
        '/v2.0/networks?tenant_id=%s' % tenant_id),
        'lbaas':('loadbalancers', 'neutron', '/v2.0/lbaas/loadbalancers'),
        'cinder':('cinder', 'cinderv2' , '/volumes/detail'),
        'glance':('glance', 'glance' , '/v2/images?limit=1'),
        'heat':('heat', 'heat' , '/stacks'),
        'swift':('swift', 'swift' , '?format=json'),
        'ceilometer':('ceilometer', 'ceilometer' , '/v2/meters/cpu?limit=1'),
        'service-list':('service-list', 'nova', '/os-services')
    }

    endpoint = endpoints[urls[args.service_type][1]] + urls[args.service_type][2]
    r, metric_data = request(metric_data, scheme, endpoint,
                             timestamp, headers=headers )

    if args.service_type == 'service-list':
        metric_data = []
        metric_data = service_list_metric(r.json()['services'], metric_data, scheme)


    print_metric(metric_data)
    sys.exit(STATE_OK)

if __name__ == "__main__":
    main()
