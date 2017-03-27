#!/usr/bin/python
#
# Copyright 2014, Craig Tracey <craigtracey@gmail.com>
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

import json
import re

from sensu_plugin import SensuPluginCheck
from subprocess import check_output, CalledProcessError, STDOUT

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2

STATE_STR = {STATE_OK: 'OK', STATE_WARNING: 'WARNING', STATE_CRITICAL: 'CRITICAL' }

class SwiftDispersionCheck(SensuPluginCheck):

    def setup(self):
        self.parser.add_argument('-c', '--container-crit', type=int, default=98,
                                 help='Container critical dispersion percent')
        self.parser.add_argument('-d', '--container-warn', type=int, default=99,
                                 help='Container warning dispersion percent')
        self.parser.add_argument('-o', '--object-crit', type=int, default=98,
                                 help='Object critical dispersion percent')
        self.parser.add_argument('-n', '--object-warn', type=int,  default=99,
                                 help='Object warning dispersion percent')
        self.parser.add_argument('-i', '--insecure', dest='insecure', default=False,
                                 action='store_true', help='ignore SSL')
        self.parser.add_argument('-z', '--criticality', type=str, default='critical',
                                 help='highest alert level')

    def run(self):

        output = None
        try:
            if self.options.insecure:
                output = check_output(['swift-dispersion-report', '-j', 
				                       '--insecure' ], stderr=STDOUT)
            else:
                output = check_output(['swift-dispersion-report', '-j' ],
                                        stderr=STDOUT)

            # strip any ERRORs that come through
            p = re.compile(r'(\{.*\})')
            m = p.search(output)
            output = m.group(1)

        except CalledProcessError as e:
            self.critical("Unable to run swift-dispersion-check: %s %s" %
                          (e, output))
            return

        dispersion = json.loads(output)

        msg = "Swift %s dispersion %d < %s threshold. "
        output = ""
        container_state = STATE_OK
        object_state = STATE_OK
        if self.options.criticality == 'critical':
            alert_level = STATE_CRITICAL  
        else:
            alert_level = STATE_WARNING

        if dispersion['container'] is not None:
            container_pct = int(dispersion['container']['pct_found'])
            if self.options.container_crit > container_pct:
                container_state = STATE_CRITICAL
            elif self.options.container_warn > container_pct:
                container_state = STATE_WARNING
            if container_state:
                output = msg % ('container', container_pct, STATE_STR[container_state]) 

        if dispersion['object'] is not None:
            object_pct = int(dispersion['object']['pct_found'])
            if self.options.object_crit > object_pct:
                object_state = STATE_CRITICAL
            elif self.options.object_warn > object_pct:
                object_state = STATE_WARNING	
            if object_state:
                output += msg % ('object', object_pct, STATE_STR[object_state]) 				
		
        output_state = min(max(container_state, object_state), alert_level)
        if output_state == STATE_CRITICAL:
            self.critical(output)
        elif output_state == STATE_WARNING:
            self.warning(output)
        else:
            self.ok()

if __name__ == "__main__":
    SwiftDispersionCheck()
