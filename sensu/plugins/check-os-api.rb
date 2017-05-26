#!/usr/bin/env /opt/sensu/embedded/bin/ruby
#
# Check OS API
# ===
#
# Purpose: to check openstack service api endpoint.
#
# Released under the same terms as Sensu (the MIT license); see LICENSE
# for details.

require 'rubygems' if RUBY_VERSION < '1.9.0'
require 'sensu-plugin/check/cli'

class CheckOSApi < Sensu::Plugin::Check::CLI
  option :service, :long  => '--service SERVICE_TYPE'

  option :criticality,
         :short => '-z CRITICALITY',
         :long => '--criticality CRITICALITY',
         :default => 'critical'
  ##
  # Build a command to execute, since this is passed directly
  # to Kernel#system.

  def safe_command
    cmd = case config[:service]
    when "nova"
      "openstack server list --limit 1"
    when "glance"
      "openstack image list --limit 1"
    when "keystone"
      "openstack endpoint list"
    when "heat"
      "openstack stack list --limit 1"
    when "ceilometer"
      "ceilometer meter-list -l 1"
    when "barbican"
      "openstack secret list -l 1"
    end
  end

  def run
    system("#{safe_command}" + " > /dev/null ")

    if $?.exitstatus == 0
      exit
    elsif config[:criticality] == 'warning'
      warning
    else
      critical
    end
  end
end
