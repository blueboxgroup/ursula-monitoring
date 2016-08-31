#! /opt/sensu/embedded/bin/ruby
#
# check-ceph-usage
#
# DESCRIPTION:
#   Raise alert if ceph cluster %RAW used exceed threshold
#
# OUTPUT:
#   plain text, eixt code 0: OK, 1:Warning, 2:Critical, Others:Unknown
#
# PLATFORMS:
#   Linux
#
# DEPENDENCIES:
#   gem: sensu-plugin
#   ceph client
#
# USAGE:
#   #YELLOW
#
# NOTES:
#   Runs 'ceph df' command(s) to report usage of ceph cluster. May 
#   need read access to ceph keyring and/or root access for 
#   authentication.
#
#   Using -z (--criticality) option to change criticality level. 
#   if criticality is warning, raise warning alert; or raise critical
#   alert.
#
#   Using -t (--threshold) option to determine alert level. 
#   >= threshold, raise alert
#
# LICENSE:
#   Copyright 2013 Brian Clark <brian.clark@cloudapt.com>
#   Released under the same terms as Sensu (the MIT license); see LICENSE
#   for details.
#

require 'rubygems' if RUBY_VERSION < '1.9.0'
require 'sensu-plugin/check/cli'
require 'timeout'
require 'English'
require 'json'

class CheckCephClusterUsage < Sensu::Plugin::Check::CLI
  option :keyring,
         description: 'Path to cephx authentication keyring file',
         short: '-k KEY',
         long: '--keyring',
         proc: proc { |k| " -k #{k}" }

  option :monitor,
         description: 'Optional monitor IP',
         short: '-m MON',
         long: '--monitor',
         proc: proc { |m| " -m #{m}" }

  option :cluster,
         description: 'Optional cluster name',
         short: '-c NAME',
         long: '--cluster',
         proc: proc { |c| " --cluster=#{c}" }

  option :timeout,
         description: 'Timeout (default 10)',
         short: '-t SEC',
         long: '--timeout',
         proc: proc(&:to_i),
         default: 10

  option :threshold,
         short: '-w PERCENT',
		 long: '--threshold',
         proc: proc {|a| a.to_i },
         default: 75
	
  option :criticality,
         description: 'Set criticality level, critical is default',
         short: '-z criticality',
         long: '--criticality criticality',
         default: 'critical'
		 
  option :verbose,
         description: 'Show cluster usage (verbose!)',
         short: '-v',
         long: '--verbose',
         boolean: true,
         default: false

  def run_cmd(cmd)
    pipe, status = nil
    begin
      cmd += config[:cluster] if config[:cluster]
      cmd += config[:keyring] if config[:keyring]
      cmd += config[:monitor] if config[:monitor]
      cmd += ' 2>&1'
      Timeout.timeout(config[:timeout]) do
        pipe = IO.popen(cmd)
        Process.wait(pipe.pid)
        status = $CHILD_STATUS.exitstatus
      end
    rescue Timeout::Error
      begin
        Process.kill(9, pipe.pid)
        Process.wait(pipe.pid)
      rescue Errno::ESRCH, Errno::EPERM
        # Catch errors from trying to kill the timed-out process
        # We must do something here to stop travis complaining
        if config[:criticality] == 'warning'
          warning 'Execution timed out'
        else
          critical 'Execution timed out'
        end
      ensure
        if config[:criticality] == 'warning'
          warning 'Execution timed out'
        else
          critical 'Execution timed out'
        end
      end
    end

    output = pipe.read
    if config[:criticality] == 'warning'
      warning "Command '#{cmd}' returned no output" if output.to_s == ''
      warning output unless status == 0
    else
      critical "Command '#{cmd}' returned no output" if output.to_s == ''
      critical output unless status == 0
    end
    output
  end

  def run
    result = run_cmd('ceph df --format=json')
    data = JSON.parse(result)
    used_percentage = data['stats']['total_used_bytes'] * 100.0 / data['stats']['total_bytes']
    
    output = '%RAW Used: ' + used_percentage.to_s
    output = output + '  ' + result if config[:verbose]
    
    if used_percentage >= config[:threshold]
      warning output if config[:criticality] == 'warning'
      critical output
    end
    
    ok output
	
  end
end
