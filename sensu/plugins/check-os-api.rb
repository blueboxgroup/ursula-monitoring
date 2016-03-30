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
      "nova list"
    when "glance"
      "glance image-list"
    when "keystone"
      "keystone endpoint-list"
    when "heat"
      "heat stack-list"
    when "ceilometer"
      "ceilometer meter-list"
    end
  end

  def run
    system("#{safe_command}")

    if $?.exitstatus == 0
      exit
    elsif config[:criticality] == 'warning'
      warning
    else
      critical
    end
  end
end
