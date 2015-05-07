#! /usr/bin/env ruby

require 'rubygems' if RUBY_VERSION < '1.9.0'
require 'sensu-plugin/check/cli'

class CheckNetworkStats < Sensu::Plugin::Check::CLI

    linkspeed = "ethtool eth0 | grep Speed"
    if linkspeed.include? "10000Mb"
  option :warn,
    :short => '-w WARN',
    :proc => proc {|a| a.to_i },
    :default => 900000
  option :crit,
    :short => '-c CRIT',
    :proc => proc {|a| a.to_i },
    :default => 1200000
    else
  option :warn,
    :short => '-w WARN',
    :proc => proc {|a| a.to_i },
    :default => 90000
  option :crit,
    :short => '-c CRIT',
    :proc => proc {|a| a.to_i },
    :default => 120000
    end
  option :rxmcswarn,
    :short => '-pw WARN',
    :proc => proc {|a| a.to_i },
    :default => 9000
  option :rxmcscrit,
    :short => '-pc CRIT',
    :proc => proc {|a| a.to_i },
    :default => 10000

  def run
    `sar -n DEV 5 1 | grep Average | grep "eth0 "`.each_line do |line|  # rubocop:disable Style/Next
      stats = line.split
      unless stats.empty?
        stats.shift 
        nic = stats.shift
        stats.map! { |x| x.to_f }
        rxpck, txpck, rxkB, txkB, rxcmp, txcmp, rxmcs = stats

        msg = "\nIngress kB/s=#{rxkB} \nEgress kB/s=#{txkB} \nIngress multicast packets per second=#{rxmcs}"
        message msg

        warning if rxkB >= config[:warn] or rxkB <= -config[:warn]
        warning if txkB >= config[:warn] or txkB <= -config[:warn]
        warning if rxmcs >= config[:rmcswarn] or rxmcs <= -config[:rmcswarn]
        critical if rxkB >= config[:crit] or rxkB <= -config[:crit]
        critical if txkB >= config[:crit] or txkB <= -config[:crit]
        critical if rxmcs >= config[:rxmcscrit] or rxmcs <= -config[:rxmcscrit]

        ok
      end
    end
  end
end
