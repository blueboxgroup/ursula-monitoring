#!/bin/bash

while getopts 'z:' OPT; do
  case $OPT in
    z)  CRITICALITY=$OPTARG;;
  esac
done

CRITICALITY=${CRITICALITY:-critical}

set -e
if nova-manage service list | tail -n +2 | grep XXX; then
  echo "a nova service is down"
  if [ "$CRITICALITY" == "warning" ]; then
    exit 1
  else
    exit 2
  fi
fi
exit 0
