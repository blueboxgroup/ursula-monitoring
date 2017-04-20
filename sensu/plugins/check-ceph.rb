#! /opt/sensu/embedded/bin/ruby
#
# check-ceph
#
# DESCRIPTION:
#   #YELLOW
#
# OUTPUT:
#   plain text
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
#   Runs 'ceph health' command(s) to report health status of ceph
#   cluster. May need read access to ceph keyring and/or root access
#   for authentication.
#
#   Using -i (--ignore-flags) option allows specific options that are
#   normally considered Ceph warnings to be overlooked and considered
#   as 'OK' (e.g. noscrub,nodeep-scrub).
#
#   Using -d (--detailed) and/or -o (--osd-tree) and/or -f (--osd-df)
#   and/or -p (--osd-perf) will dramatically increase
#   verboseness during warning/error reports, however they may add
#   additional insights to cluster-related problems during notification.
#
#   Using -e (--escalate_flags) option allows specific options that are
#   normally consdiered Ceph warning to be escalated and considered as
#   'ERR' (e.g. osds are down,near full osd,clock skew,mons down)
#
#   Using -z (--criticality) option to change criticality level.
#   if criticality is warning, all Critical change to be Warning.
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

class CheckCephHealth < Sensu::Plugin::Check::CLI
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

  option :ignore_flags,
         description: 'Optional ceph warning flags to ignore',
         short: '-i FLAG[,FLAG]',
         long: '--ignore-flags',
         proc: proc { |f| f.split(',') }

  option :escalate_flags,
         description: 'Optional ceph warning flags to critical',
         short: '-e FLAG[,FLAG]',
         long: '--escalate-flags',
         proc: proc { |f| f.split(',') }

  option :show_detail,
         description: 'Show ceph health detail on warns/errors (verbose!)',
         short: '-d',
         long: '--detailed',
         boolean: true,
         default: false

  option :osd_tree,
         description: 'Show OSD tree on warns/errors (verbose!)',
         short: '-o',
         long: '--osd-tree',
         boolean: true,
         default: false

  option :osd_df,
         description: 'Show OSD utilization (verbose!)',
         short: '-f',
         long: '--osd-df',
         boolean: true,
         default: false

  option :osd_perf,
         description: 'Show OSD performance (verbose!)',
         short: '-p',
         long: '--osd-perf',
         boolean: true,
         default: false

   option :criticality,
          description: 'Set criticality level, critical is default',
          short: '-z criticality',
          long: '--criticality criticality',
          default: 'critical'

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

  def strip_warns(result)
    r = result.dup
    r.gsub!(/HEALTH_WARN\ /, '')
     .gsub!(/\ ?flag\(s\) set/, '')
     .gsub!(/\n/, '')
    config[:ignore_flags].each do |f|
      r.gsub!(/,?#{f},?/, '')
    end
    if r.length == 0
      result.gsub(/HEALTH_WARN/, 'HEALTH_OK')
    else
      result
    end
  end

  def check_ceph_health
    if config[:show_detail]
      run_cmd('ceph health detail')
    else
      run_cmd('ceph health')
    end
  end

  def run
    result = check_ceph_health
    osd_down_count = run_cmd('ceph osd tree | grep down | wc -l').to_i
    unless result.start_with?('HEALTH_OK')
      result = strip_warns(result) if config[:ignore_flags]
    end
    ok result if result.start_with?('HEALTH_OK') and osd_down_count==0

    result += run_cmd('ceph osd tree') if config[:osd_tree] and (result.include?('osds are down') or osd_down_count>0)
    result += run_cmd('ceph osd df') if config[:osd_df] and result.include?('full osd')
    result += run_cmd('ceph osd perf') if config[:osd_perf] and result.include?('requests are blocked')

    warning result if config[:criticality] == 'warning'
    critical result if result.start_with?('HEALTH_ERR')

    # set config[:escalate_flags] default as 'near full osd' if no escalate_flags options provided.
    config[:escalate_flags]=['near full osd','osds are down','clock skew','mons down'] unless config[:escalate_flags]
    # escalate optional warning to critical
    config[:escalate_flags].each do |p|
      critical result if result.include?(p)
    end

    critical result if osd_down_count>0
    warning result

  end
end
