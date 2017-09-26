#!/usr/bin/env /opt/sensu/embedded/bin/ruby
##
## Check dedicated controller ethernet tuning
##

require 'rubygems' if RUBY_VERSION < '1.9.0'
require 'sensu-plugin/check/cli'

class CheckControllerTuning < Sensu::Plugin::Check::CLI
  def run
    cmd = "/sbin/ethtool -n eth0 rx-flow-hash udp4 | grep -q 'L4 bytes'"
    if system(cmd)
      ok
    else
      msg = "the ethernet-tuning service is disabled"
      critical msg
    end
  end
end
