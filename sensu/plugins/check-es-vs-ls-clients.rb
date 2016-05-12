#!/opt/sensu/embedded/bin/ruby
#
#  check-es-vs-ls-clients
#
# DESCRIPTION:
#   This plugin uses the ES APIs to determine if there's enough
#   raw space on elk nodes to support number of logstash clients.
#   hopefully it provides useful hints about when to scale ELK.
#
# OUTPUT:
#   plain text
#
# PLATFORMS:
#   Linux
#
# DEPENDENCIES:
#   gem: sensu-plugin
#   gem: elasticsearch
#
# USAGE:
#   #YELLOW
#
# NOTES:
#
# LICENSE:
#   Copyright 2016 IBM
#   Copyright 2012 Sonian, Inc <chefs@sonian.net>
#   Released under the same terms as Sensu (the MIT license); see LICENSE
#   for details.
#

require 'rubygems' if RUBY_VERSION < '1.9.0'
require 'sensu-plugin/check/cli'
require 'elasticsearch'
require 'json'
require 'pp'
require 'date'

$query = <<-eos
{
  "size": 0,
  "query": {
    "filtered": {
      "query": {
        "query_string": {
          "query": "*",
          "analyze_wildcard": true
        }
      },
      "filter": {
        "bool": {
          "must": [
          ],
          "must_not": []
        }
      }
    }
  },
  "aggs": {
    "1": {
      "cardinality": {
        "field": "host"
      }
    }
  }
}
eos

class ESClusterStatus < Sensu::Plugin::Check::CLI
  option :bytes,
         description: 'How many bytes to allow for per host per day',
         short: '-b BYTES',
         long: '--bytes BYTES',
         proc: proc(&:to_i),
         default: 130000000 # 130mb

  option :days,
         description: 'How many days expected to keep logs for',
         short: '-d DAYS',
         long: '--days DAYS',
         proc: proc(&:to_i),
         default: 270

  option :index,
         description: 'elasticsearch index[es] to search',
         short: '-i INDEX',
         long: '--index INDEX',
         default: (Date.today-1).strftime("logstash-%Y.%m.%d")

  def run
    client = Elasticsearch::Client.new log: false
    space = 0
    node_stats = client.nodes.stats

    node_stats['nodes'].each do |node,data|
      data['fs']['data'].each do |disk|
        space += disk['total_in_bytes']
      end
    end

    count_nodes = client.search index: config[:index], body: $query
    nodes = count_nodes['aggregations']['1']['value'].to_i
    allowance = config[:bytes] * config[:days] * nodes
    raw_space_per_node = space / nodes / config[:days]
    max_nodes_for_space = space / config[:bytes] / config[:days]

    puts "you have #{raw_space_per_node/1000} bytes available per known logstash client. You should have > #{config[:bytes]/1000}.  You can support approximately #{max_nodes_for_space} logstash clients."

    if max_nodes_for_space <= nodes
      puts "you need to scale your ELK cluster"
      critical
    else
      ok
    end

  end
end
