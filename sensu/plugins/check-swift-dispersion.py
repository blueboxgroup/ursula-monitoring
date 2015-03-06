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


class SwiftDispersionCheck(SensuPluginCheck):

    def setup(self):
        self.parser.add_argument('-c', '--container-crit', type=int,
                                 help='Container critical dispersion percent')
        self.parser.add_argument('-d', '--container-warn', type=int,
                                 help='Container warning dispersion percent')
        self.parser.add_argument('-o', '--object-crit', type=int,
                                 help='Object critical dispersion percent')
        self.parser.add_argument('-n', '--object-warn', type=int,
                                 help='Object warning dispersion percent')

    def run(self):

        output = None
        try:
            output = check_output(['swift-dispersion-report', '-j'],
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
        container_pct = int(dispersion['container']['pct_found'])
        object_pct = int(dispersion['object']['pct_found'])

        msg = "Swift %s dispersion %s threshold %d > %d"
        if ((self.options.container_crit and
             self.options.container_crit > container_pct)):
            self.critical(msg % ('container', 'CRITICAL',
                                 self.options.container_crit, container_pct))
        elif ((self.options.object_crit and
               self.options.object_crit > object_pct)):
            self.critical(msg % ('object', 'CRITICAL',
                                 self.options.object_crit, object_pct))
        elif ((self.options.container_warn and
               self.options.container_warn > container_pct)):
            self.critical(msg % ('container', 'WARNING',
                                 self.options.container_warn, container_pct))
        elif ((self.options.object_warn and
               self.options.object_warn > object_pct)):
            self.critical(msg % ('object', 'WARNING',
                                 self.options.object_warn, object_pct))
        else:
            self.ok()

if __name__ == "__main__":
    SwiftDispersionCheck()
