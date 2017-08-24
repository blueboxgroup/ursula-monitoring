#!/opt/sensu/embedded/bin/ruby
#
#   netif-metrics
#
# DESCRIPTION:
#   Network interface throughput
#
# OUTPUT:
#   metric data
#
# PLATFORMS:
#   Linux
#
# DEPENDENCIES:
#   gem: sensu-plugin
#
# USAGE:
#   #YELLOW
#
# NOTES:
#
# LICENSE:
#   Copyright 2014 Sonian, Inc. and contributors. <support@sensuapp.org>
#   Released under the same terms as Sensu (the MIT license); see LICENSE
#   for details.
#

require 'sensu-plugin/check/cli'
require 'socket'

#
# Netif Metrics
#
class NetIFMetrics < Sensu::Plugin::Check::CLI
  option :interfaces,
         description: 'list of interfaces to check',
         long: '--interfaces [eth0,eth1]',
         default: 'eth0'
  option :warn,
         short: '-w Mbps',
         default: 250,
         description: 'Warning Mbps, default: 250'
  option :crit,
         short: '-c Mbps',
         default: 500,
         description: 'Critical Mbps, default: 500'
  option :interval,
         descrption: 'how many seconds to collect data for',
         long: '--interval 1',
         default: 1

  def run
    if config[:crit].include? '%'
      config[:crit] = config[:crit].sub( '%$', '' )
      config[:crit] = config[:crit].to_f / 100
    else
      config[:crit] = config[:crit].to_i
    end

    if config[:warn].include? '%'
      config[:warn] = config[:warn].sub( '%$', '' )
      config[:warn] = config[:warn].to_f / 100
    else
      config[:warn] = config[:warn].to_i
    end

    `sar -n DEV #{config[:interval]} 1 | grep Average | grep -v IFACE`.each_line do |line|  # rubocop:disable Style/Next
      stats = line.split(/\s+/)
      unless stats.empty?
        stats.shift
        nic = stats.shift
        if config[:interfaces].include? nic
          linkspeed = `ethtool #{nic} 2>/dev/null | awk '$1 == "Speed:" { print int($2) }'`.to_i
          rx_mbps = ( stats[2].to_f * 8 ) / 1000
          tx_mbps = ( stats[3].to_f * 8 ) / 1000
          if ( config[:crit].is_a?( Float ) && ( rx_mbps > ( config[:crit] * linkspeed ) || tx_mbps > ( config[:crit] * linkspeed ) ) )
            status = "#{nic} #{rx_mbps} rx_mbps or #{tx_mbps} tx_mbps is higher than " + ( config[:crit] * linkspeed ).to_i.to_s
            critical status
          elsif ( config[:crit].is_a?( Integer ) && ( rx_mbps > config[:crit] || tx_mbps > config[:crit] ) )
            status = "#{nic} #{rx_mbps} rx_mbps or #{tx_mbps} tx_mbps is higher than " + config[:crit].to_s
            critical status
          elsif ( config[:warn].is_a?( Float ) && ( rx_mbps > ( config[:warn] * linkspeed ) || tx_mbps > ( config[:warn] * linkspeed ) ) )
            status = "#{nic} #{rx_mbps} rx_mbps or #{tx_mbps} tx_mbps is higher than " + ( config[:warn] * linkspeed ).to_i.to_s
            warning status
          elsif ( config[:warn].is_a?( Integer ) && ( rx_mbps > config[:warn] || tx_mbps > config[:warn] ) )
            status = "#{nic} #{rx_mbps} rx_mbps or #{tx_mbps} tx_mbps is higher than " + config[:warn].to_s
            warning status
          end
        end
      end
    end
    exit
  end
end
