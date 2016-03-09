#!/opt/sensu/embedded/bin/ruby
#
#   check-serverspec
#
# DESCRIPTION:
#   Runs http://serverspec.org/ spec tests against your servers.
#   Fails with a warning or a critical if tests are failing, depending
#     on the severity level set.
#
# OUTPUT:
#   plain text
#
# PLATFORMS:
#   Linux
#
# DEPENDENCIES:
#   gem: sensu-plugin
#   gem: json
#   gem: socket
#   gem: serverspec
#
# USAGE:
#   Run entire suite of testd
#   check-serverspec -d /etc/my_tests_dir
#
#   Run only one set of tests
#   check-serverspec -d /etc/my_tests_dir -t spec/test_one
#
#   Run with a warning severity level
#   check-serverspec -d /etc/my_tests_dir -s warning
#
# NOTES:
#   Does it behave differently on specific platforms, specific use cases, etc
#   Critical severity level is set as the default 
#
# LICENSE:
#   Copyright 2014 Sonian, Inc. and contributors. <support@sensuapp.org>
#   Released under the same terms as Sensu (the MIT license); see LICENSE
#   for details.
#

require 'json'
require 'socket'
require 'digest/sha1'
require 'serverspec'
require 'sensu-plugin/check/cli'

#
#
#
class CheckServerspec < Sensu::Plugin::Check::CLI
  option :tests_dir,
         short: '-d /tmp/dir',
         long: '--tests-dir /tmp/dir',
         required: true

  option :spec_tests,
         short: '-t spec/test',
         long: '--spec-tests spec/test',
         default: nil

  option :handler,
         short: '-l HANDLER',
         long: '--handler HANDLER',
         default: 'default'

  option :severity,
         short: '-s severity',
         long: '--severity severity',
         default: 'critical'

  def sensu_client_socket(msg)
    u = UDPSocket.new
    u.send(msg + "\n", 0, '127.0.0.1', 3030)
  end

  def send_ok(check_name, msg)
    d = { 'name' => check_name, 'status' => 0, 'output' => 'OK: ' + msg, 'handler' => config[:handler] }
    sensu_client_socket d.to_json
  end

  def send_warning(check_name, msg)
    d = { 'name' => check_name, 'status' => 1, 'output' => 'WARNING: ' + msg, 'handler' => config[:handler] }
    sensu_client_socket d.to_json
  end

  def send_critical(check_name, msg)
    d = { 'name' => check_name, 'status' => 2, 'output' => 'CRITICAL: ' + msg, 'handler' => config[:handler] }
    sensu_client_socket d.to_json
  end

  def run
    serverspec_results = `cd #{config[:tests_dir]} ; /opt/sensu/embedded/bin/rspec #{config[:spec_tests]} --format json`
    parsed = JSON.parse(serverspec_results)

    parsed['examples'].each do |serverspec_test|
      example_uniq_hash = Digest::SHA1.hexdigest serverspec_test['full_description']
      test_name = serverspec_test['file_path'].split('/')[-1] + '_' + example_uniq_hash
      output = serverspec_test['full_description'].gsub!(/\"/, '')

      if serverspec_test['status'] == 'passed'
        send_ok(
          test_name,
          output
        )
      else
        send_warning(
          test_name,
          output
        )
      end
    end

    puts parsed['summary_line']
    failures = parsed['summary_line'].split[2]
    if failures != '0'
      if config[:severity] == 'warning'
        exit_with(
          :warning,
          parsed['summary_line']
        )
      else
        exit_with(
          :critical,
          parsed['summary_line']
        )
      end
    else
      exit_with(
        :ok,
        parsed['summary_line']
      )
    end
  end

  def exit_with(sym, message)
    case sym
    when :ok
      ok message
    when :warning
      warning message
    when :critical
      warning critical
    else
      unknown message
    end
  end
end
