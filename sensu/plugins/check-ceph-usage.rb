#! /opt/sensu/embedded/bin/ruby
#
# check-ceph-usage
#
# DESCRIPTION:
#   Raise alert if ceph pool %used exceed threshold
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
#   Using -p (--pool) option to determine specific pools to check. 
#   if not be provided, then all pools will be checked.
#
# Code adapted from Brian Clark's script in the Sensu Plugins community:
# https://github.com/sensu-plugins/sensu-plugins-ceph/blob/master/bin/check-ceph.rb
# with modification to support pool usage check.
#
# Released under the same terms as Sensu (the MIT license); see MITLICENSE
# for details.
#
# Xiao Hua, Shen <shenxh@cn.ibm.com>

require 'rubygems' if RUBY_VERSION < '1.9.0'
require 'sensu-plugin/check/cli'
require 'timeout'
require 'English'
require 'json'

class CheckCephPoolUsage < Sensu::Plugin::Check::CLI
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
  
  option :pool,
         description: 'only check specific pools',
         short: '-p POOL',
         long: '--pools POOL',
         proc: proc {|a| a.split(',') }

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
    crit_pool = []
    output = ''

    data['pools'].each do | pool |
      next if config[:pool] && !config[:pool].include?(pool['name'])
      usage = pool['stats']['bytes_used'] * 100.0 /(pool['stats']['bytes_used'] + pool['stats']['max_avail'])
      crit_pool << "#{pool['name']} #{usage}%" if usage >= config[:threshold]
    end unless result.to_s == ''

    ok "All Pools usage under #{config[:threshold]}%" if crit_pool.empty?

    output = crit_pool.join(', ')
    output = output + "\n" + result if config[:verbose]

    warning output if config[:criticality] == 'warning'
    critical output

  end
end
