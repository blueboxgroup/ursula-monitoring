#!/usr/bin/env /opt/sensu/embedded/bin/ruby
#
# Openstack Keystone expired token Plugin
# ===
#
# This plugin checks the number of expired token in Keystone and warns you according to specified limits
#
# Released under the same terms as Sensu (the MIT license); see LICENSE
# for details.


require 'rubygems' if RUBY_VERSION < '1.9.0'
require 'sensu-plugin/check/cli'

class CheckKeystoneExpiredToken < Sensu::Plugin::Check::CLI

  option  :warning,
          :description => "warning count of expired token",
          :short => '-w NUMBER',
          :long => '--warning NUMBER',
          :proc => proc {|a| a.to_i },
          :default => 1000
		  
  option  :critical,
          :description => "critical count of expired token",
          :short => '-c NUMBER',
          :long => '--critical NUMBER',
          :proc => proc {|a| a.to_i },
          :default => 10000

  option  :criticality,
          :description => "Set sensu alert level, default is critical",
          :short => '-z CRITICALITY',
          :long => '--criticality CRITICALITY',
          :default => 'critical'
		  
  option  :defaults_file,
          :description => "mysql defaults file",
          :short => '-d DEFAULTS_FILE',
          :long => '--defaults-file DEFAULTS_FILE',
          :default => '/root/.my.cnf'

  def run
    expired_token_count = `mysql --defaults-file=#{config[:defaults_file]} -N -s -e "select count(*) from keystone.token where expires<now()"`
    expired_token_count.strip!
    msg = "#{expired_token_count} expired token found"
    
    ok msg if expired_token_count.to_i < config[:warning]
    critical msg if expired_token_count.to_i >= config[:critical] and config[:criticality] == 'critical'
    warning msg

  end
end
