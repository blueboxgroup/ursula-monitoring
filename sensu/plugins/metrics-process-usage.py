#!/usr/bin/env python
#
#  metrics-process-usage.py
#
# PLATFORMS:
#   Linux
#
# DEPENDENCIES:
#  Python 2.7+ (untested on Python3, should work though)
#  Python module: psutil https://pypi.python.org/pypi/psutil
#
# USAGE:
#
#  metrics-process-usage.py -n <process_name> -w <cpu_warning_pct> -c <cpu_critical_pct> -W <mem_warning_pct> -C <mem_critical_pct> [-s <graphite_scheme>]
#
# DESCRIPTION:
# Finds the pid[s] corresponding to a process name and obtains the necessary
# cpu and memory usage stats. Returns WARNING or CRITICAL when these stats
# exceed user specified limits.
#
# Code adapted from Jaime Gogo's script in the Sensu Plugins community:
# https://github.com/sensu-plugins/sensu-plugins-process-checks/blob/master/bin/metrics-per-process.py
#
# Released under the same terms as Sensu (the MIT license); see MITLICENSE
# for details.
#
# Siva Mullapudi <scmullap@us.ibm.com>

import optparse
import sys
import os
import time
import psutil
from collections import Counter

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2

PROC_ROOT_DIR = '/proc/'

def find_pids_from_name(process_name):
    '''Find process PID from name using /proc/<pids>/comm'''

    pids_in_proc = [ pid for pid in os.listdir(PROC_ROOT_DIR) if pid.isdigit() ]
    pids = []
    for pid in pids_in_proc:
        path = PROC_ROOT_DIR + pid
        if 'comm' in os.listdir(path):
            file_handler = open(path + '/comm', 'r')
            if file_handler.read().rstrip() == process_name:
                pids.append(int(pid))
    return pids

def stats_per_pid(pid):
    '''Gets process stats, cpu and memory usage in %, using the psutil module'''

    stats = {}
    process_handler = psutil.Process(pid)
    stats['cpu.percent'] = process_handler.cpu_percent()
    stats['memory.percent'] = process_handler.memory_percent()

    return stats

def multi_pid_process_stats(pids):
    stats = {'total_processes': len(pids)}
    for pid in pids:
        stats = Counter(stats) + Counter(stats_per_pid(pid))
        return stats

def graphite_printer(stats, graphite_scheme):
    now = time.time()
    for stat in stats:
        print "%s.%s %s %d" % (graphite_scheme, stat, stats[stat], now)

def main():
    parser = optparse.OptionParser()

    parser.add_option('-n', '--process-name',
        help    = 'name of process to collect stats (imcompatible with -p)',
        dest    = 'process_name',
        metavar = 'PROCESS_NAME')

    parser.add_option('-w', '--cpu_warning',
        help    = 'cpu percent threshold to indicate a warning',
        dest    = 'cpu_warning_pct',
        metavar = 'CPU_WARNING_PERCENT')

    parser.add_option('-c', '--cpu_critical',
        help    = 'cpu percent threshold to indicate a critical situation',
        dest    = 'cpu_critical_pct',
        metavar = 'CPU_CRITICAL_PERCENT')

    parser.add_option('-W', '--memory_warning',
        help    = 'memory percent threshold to indicate a warning',
        dest    = 'mem_warning_pct',
        metavar = 'MEMORY_WARNING_PERCENT')

    parser.add_option('-C', '--memory_critical',
        help    = 'memorypercent threshold to indicate a critical situation',
        dest    = 'mem_critical_pct',
        metavar = 'MEMORY_CRITICAL_PERCENT')

    parser.add_option('-s', '--scheme',
        help    = 'graphite scheme to prepend, default to <process_stats>',
        default = 'per_process_stats',
        dest    = 'graphite_scheme',
        metavar = 'GRAPHITE_SCHEME')

    (options, args) = parser.parse_args()

    pids = find_pids_from_name(options.process_name)

    if not pids:
        print 'Cannot find pids for this process. Enter a valid process name.'
        sys.exit(STATE_CRITICAL)

    if not options.cpu_warning_pct or not options.cpu_critical_pct \
       or not options.mem_warning_pct or not options.mem_critical_pct:
        print 'Failed to specify a percentage limit.'
        sys.exit(STATE_CRITICAL)

    total_process_stats = multi_pid_process_stats(pids)
    graphite_printer(total_process_stats, options.graphite_scheme)

    if total_process_stats['cpu.percent'] > float(options.cpu_critical_pct) or \
       total_process_stats['memory.percent'] > float(options.mem_critical_pct):
       print 'CPU Usage and/or memory usage at critical levels!!!'
       sys.exit(STATE_CRITICAL)

    if total_process_stats['cpu.percent'] > float(options.cpu_warning_pct) or \
       total_process_stats['memory.percent'] > float(options.mem_warning_pct):
       print 'Warning: CPU Usage and/or memory usage exceeding normal levels!'
       sys.exit(STATE_WARNING)

    sys.exit(STATE_OK)

if __name__ == "__main__":
    main()

