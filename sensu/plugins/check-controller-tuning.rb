#!/usr/bin/env /opt/sensu/embedded/bin/ruby
##
## Check dedicated controller ethernet tuning
##

require 'rubygems' if RUBY_VERSION < '1.9.0'
require 'sensu-plugin/check/cli'

class CheckControllerTuning < Sensu::Plugin::Check::CLI
  def run
    tuning_status = `service ethernet-tuning status`
    msg = "the ethernet-tuning service is disabled"
    critical msg if tuning_status.include?("disabled")
    ok
  end
end
