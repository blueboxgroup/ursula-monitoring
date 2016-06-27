#!/bin/bash

while getopts 'z:' OPT; do
  case $OPT in
    z)  CRITICALITY=$OPTARG;;
  esac
done

CRITICALITY=${CRITICALITY:-critical}

set -e
source /etc/sensu/stackrc
if nova service-list | tail -n +4 | grep -v '^+-' | cut -d'|' -f 3,7 | grep down; then
  echo "a nova service is down"
  if [ "$CRITICALITY" == "warning" ]; then
    exit 1
  else
    exit 2
  fi
fi
exit 0
