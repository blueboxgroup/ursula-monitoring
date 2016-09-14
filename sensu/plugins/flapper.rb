#!/usr/bin/env /opt/sensu/embedded/bin/ruby
#
# Generate an event every N minutes to verify upstream functionality
#

require 'rubygems' if RUBY_VERSION < '1.9.0'
require 'sensu-plugin/check/cli'

class Flapper < Sensu::Plugin::Check::CLI

  option :duration,
    :short => '-d DURATION',
    :description => "Time until emitting next state change",
    :proc => proc {|a| a.to_i },
    :in => [1, 2, 3, 5, 10, 15],
    :default => 1

  def run
    (Time.now.min / config[:duration] % 2) == 0 ? critical : ok
  end
end
