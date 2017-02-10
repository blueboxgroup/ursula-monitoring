#! /usr/bin/env ruby
#
# metrics-ceph-pool-capacity
#
# DESCRIPTION:
#   This plugin is used to get ceph capacity metrics for using ceph as
#   OpenStack Cinder's driver. 
#   
#   *.poolname.used_bytes   using 'ceph df' to get 'bytes_used'
#   *.poolname.max_avail_bytes   using 'ceph df' to get 'max_avail'
#   *.poolname.total_bytes using 'ceph df' to get 'bytes_used'+'max_avail'
#   *.poolname.cinder_allocated_bytes  using 'rbd ls -l' to sum the 'SIZE'
#   *.poolname.cinder_avail_bytes  total_bytes - cinder_allocated_bytes
#   (suppose this ceph is only used for openstack cinder)
#
#   since ceph support thin provision, total_allocated_bytes >= total_used_bytes
#
# OUTPUT:
#   metrics data in Graphite's format
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
#   Runs 'ceph df' and 'rbd ls -l' command(s) to report usage of ceph cluster.  
#   May need read access to ceph keyring and/or root access for 
#   authentication.
#
# LICENSE:
#   Released under the same terms as Sensu (the MIT license); see LICENSE
#   for details.
#

require 'rubygems' if RUBY_VERSION < '1.9.0'
require 'sensu-plugin/metric/cli'
require 'timeout'
require 'English'
require 'json'
require 'socket'

class CephPoolCapacity < Sensu::Plugin::Metric::CLI::Graphite

  option :scheme,
    :description => "Metric naming scheme, text to prepend to .$parent.$child",
	:short => "-s SCHEME",
    :long => "--scheme SCHEME",
    :default => "#{Socket.gethostname}.ceph"

  option :timeout,
    :description => "Timeout (default 10)",
    :short => "-t SEC",
    :long => "--timeout",
    :proc => proc(&:to_i),
    :default => 10

  def run_cmd(cmd)
    pipe, status = nil
    begin
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
        exit
	  end
    end

    output = pipe.read
	exit if output.to_s == ''
    output
  end

  def print_pool_usage(data)
    metrics = Hash.new
	timestamp = Time.now.to_i
	
    data['pools'].each do | pool |  
      metrics[pool['name']] = Hash.new
      metrics[pool['name']]['used_bytes'] = pool['stats']['bytes_used']
      metrics[pool['name']]['total_bytes'] = pool['stats']['bytes_used'] + pool['stats']['max_avail']
	  metrics[pool['name']]['max_avail_bytes'] = pool['stats']['max_avail']
	  metrics[pool['name']]['used_percentage'] = pool['stats']['bytes_used'] * 100.0 / (pool['stats']['bytes_used'] + pool['stats']['max_avail'])

      allocated_result = run_cmd('rbd ls -l --format=json ' + pool['name'])
      images = JSON.parse(allocated_result)
      total_allocated_bytes = 0
  
      images.each do | image | 
        total_allocated_bytes += image['size']
      end unless allocated_result.to_s == ''
	  
      metrics[pool['name']]['cinder_allocated_bytes'] = total_allocated_bytes
	  metrics[pool['name']]['cinder_avail_bytes'] = pool['stats']['bytes_used'] + pool['stats']['max_avail'] - total_allocated_bytes
	  metrics[pool['name']]['allocated_percentage'] = total_allocated_bytes * 100.0 / (pool['stats']['bytes_used'] + pool['stats']['max_avail'])
      
    end

    metrics.each do |parent, children|
      children.each do |child, value|
        output [config[:scheme],'pool', parent, child].join("."), value, timestamp
      end
    end
  end
	
  def print_cluster_usage(data)
    metrics = Hash.new
	timestamp = Time.now.to_i
	
	metrics['cluster'] = Hash.new
	metrics['cluster']['total_used_bytes'] = data['stats']['total_used_bytes']
	metrics['cluster']['total_bytes'] = data['stats']['total_bytes']
	metrics['cluster']['total_avail_bytes'] = data['stats']['total_avail_bytes']
	metrics['cluster']['used_percentage'] = data['stats']['total_used_bytes'] * 100.0 / data['stats']['total_bytes']
 
    metrics.each do |parent, children|
      children.each do |child, value|
        output [config[:scheme], parent, child].join("."), value, timestamp
      end
    end
  end
  
  def run
    #get usage data
    result = run_cmd('ceph df --format=json')
    data = JSON.parse(result)

	print_pool_usage(data)
	print_cluster_usage(data)

    exit
	
  end
end
