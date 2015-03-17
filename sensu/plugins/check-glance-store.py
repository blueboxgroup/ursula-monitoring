#!/usr/bin/env python2.7

import argparse
import logging
import os
import pytz
import re
import sys
import time

from datetime import datetime, timedelta
from dateutil import parser

from glanceclient import client
from iso8601 import iso8601
from keystoneclient.v2_0 import client as ksclient


glance_auth = {
    'username':    os.environ['OS_USERNAME'],
    'password':    os.environ['OS_PASSWORD'],
    'tenant_name': os.environ['OS_TENANT_NAME'],
    'auth_url':    os.environ['OS_AUTH_URL'],
    'region_name': 'RegionOne',
}


argparser = argparse.ArgumentParser()
argparser.add_argument('--imagedir', help='Glance file store image directory',
                    default='/var/lib/glance/images')
options = argparser.parse_args()

store_directory = options.imagedir

if 'OS_CACERT' in os.environ.keys():
    glance_auth['ca_cert'] = os.environ['OS_CACERT']


keystone = ksclient.Client(**glance_auth)

auth_token = keystone.auth_token
endpoint = keystone.service_catalog.url_for(service_type='image',
                                            endpoint_type='publicURL')

# logging.basicConfig(level=logging.DEBUG)
glance = client.Client('2', endpoint=endpoint, token=auth_token)
glance.format = 'json'

# Fetch the list of files in store_directory matching the UUID regex
uuid_re = re.compile(
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
files = [(x, os.path.join(store_directory, x)) for x in
         os.listdir(store_directory) if uuid_re.match(x)]
files = [(x, os.path.getsize(p),
          datetime.fromtimestamp(os.path.getmtime(p), iso8601.Utc()))
         for x, p in files if os.path.isfile(p)]

# Fetch the list of glance images
glance_images = []
for x in glance.images.list():
    if x.status == 'active':
        tz_aware_time = parser.parse(x.created_at)
        glance_images.append((x.id, x.size, tz_aware_time))

# Check all active images 1 hour or older are present
time_cutoff = datetime.now(iso8601.Utc()) - timedelta(0, 3600)

result = 0

for image in [x for x in glance_images if x[2] < time_cutoff]:
    if not [x for x in files if x[0] == image[0]]:
        print "Glance image %s not found in %s" % (image[0], store_directory)
        result = 2


# Check all files have a corresponding glance image
for image_file in files:
    if not [x for x in glance_images if x[0] == image_file[0]]:
        print "Unknown file %s found in %s" % (image_file[0], store_directory)
        result = 2


# Check glance image file sizes match files
for image in glance_images:
    for image_file in [x for x in files if x[0] == image[0]]:
        if image[1] != image_file[1]:
            print "Glance image %s size differs from file on disk" % image[0]
            result = 2

if result == 0:
    print "Glance image store %s looks good" % store_directory

sys.exit(result)
