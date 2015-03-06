#!/bin/bash
set -e
if neutron agent-list -c alive | grep xxx; then
  echo "a neutron agent is down"
  exit 2
fi
exit 0
