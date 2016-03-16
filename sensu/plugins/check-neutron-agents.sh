#!/bin/bash

while getopts 'z:' OPT; do
  case $OPT in
    z)  CRITICALITY=$OPTARG;;
  esac
done

CRITICALITY=${CRITICALITY:-critical}

set -e
if neutron agent-list -c alive | grep xxx; then
  echo "a neutron agent is down"
  if [ "$CRITICALITY" == "warning" ]; then
    exit 1
  else
    exit 2
  fi
fi
exit 0
