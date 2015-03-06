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

import re

from sensu_plugin import SensuPluginCheck
from subprocess import check_output, CalledProcessError, STDOUT


class UnableToRunException(Exception):
    pass


class NimbleStorageCheck(SensuPluginCheck):

    def setup(self):
        self.parser.add_argument('-c', '--critical', type=float)
        self.parser.add_argument('-w', '--warning', type=float)
        self.parser.add_argument('-k', '--ssh-key',
                                 default='/root/.ssh/nimble',
                                 help='ssh key to use')
        self.parser.add_argument('-u', '--ssh-user', default='admin',
                                 help='ssh user to connect as')
        self.parser.add_argument('-n', '--nimble-host', required=True,
                                 help='nimble host to connect to')
        self.parser.add_argument('check', help='check to run')

    def _run_ssh_command(self, command):
        ssh_cmd = 'ssh '
        if self.options.ssh_key:
            ssh_cmd += '-i %s ' % self.options.ssh_key
        if self.options.ssh_user:
            ssh_cmd += '%s@' % self.options.ssh_user
        ssh_cmd += "%s '%s'" % (self.options.nimble_host, command)
        output = None
        try:
            output = check_output(ssh_cmd, shell=True)
        except CalledProcessError as cpe:
            self.warning("Unable to run command: '%s' output: '%s'" %
                         (ssh_cmd, output))
        return output

    def _check_load(self):
        output = self._run_ssh_command('uptime')
        match = re.match('.*load average: ([\d.]+)', output)
        if match:
            cur_load = match.group(1)
            if float(cur_load) > self.options.critical:
                self.critical('load is critical (%s > %s)' %
                              (cur_load, self.options.critical))
            elif float(cur_load) > self.options.warning:
                self.warning('load is elevated (%s > %s)' %
                             (cur_load, self.options.warning))
            else:
                self.ok()
        else:
            raise(UnableToRunException('Could not match load metrics'))

    def _check_raid(self):
        output = self._run_ssh_command('disk --list | grep HDD')
        unhealthy_disks = []
        for line in output.split('\n'):
            if not len(line):
                continue
            parts = re.split('\s+', line.strip())
            if not parts[6] == 'okay':
                unhealthy_disks.append(parts[1])
        if len(unhealthy_disks):
            self.critical("RAID problem detected for disk(s) %s" %
                          ', '.join(unhealthy_disks))
        else:
            self.ok()

    def _get_arrays(self):
        output = self._run_ssh_command('array --list | tail -n+4')
        arrays = []
        for line in output.split('\n'):
            if not len(line):
                continue
            parts = re.split('\s+', line.strip())
            arrays.append(parts[0])
        return arrays

    def _get_array_info_value(self, array, label):
        output = self._run_ssh_command('array --info %s | grep '
                                       '"%s"' % (array, label))
        parts = re.split('\s+', output.strip())
        return parts[-1]

    def _get_array_total_mb(self, array):
        return self._get_array_info_value(array, "Total array capacity (MB)")

    def _get_array_available_mb(self, array):
        return self._get_array_info_value(array, "Available space")

    def _check_array_free(self):
        arrays = self._get_arrays()
        crit_arrays = []
        warn_arrays = []
        for array in arrays:
            total_mb = self._get_array_total_mb(array)
            free_mb = self._get_array_available_mb(array)
            free_percent = 100 * float(free_mb)/float(total_mb)
            print "%s: %s mb Total, %s mb Used, %s percent free" % (array, total_mb, free_mb, free_percent)
            if self.options.critical and free_percent < self.options.critical:
                crit_arrays.append(array)
            elif self.options.warning and free_percent < self.options.warning:
                warn_arrays.append(array)

        if len(crit_arrays):
            self.critical('The following array(s) are critically low on '
                          'space: %s' % ', '.join(crit_arrays))
        elif len(warn_arrays):
            self.warning('The following array(s) are getting low on '
                         'space: %s' % ', '.join(warn_arrays))
        else:
            self.ok()

    def run(self):
        try:
            getattr(self, '_check_%s' % self.options.check)()
        except UnableToRunException as ure:
            self.warning(ure)

if __name__ == "__main__":
    NimbleStorageCheck()
