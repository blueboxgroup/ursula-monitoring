#!/bin/bash

while getopts 'z:' OPT; do
  case $OPT in
    z)  CRITICALITY=$OPTARG;;
  esac
done

CRITICALITY=${CRITICALITY:-critical}

set -e
if cinder service-list | grep "down"; then
  echo "a cinder service is down"
  if [ "$CRITICALITY" == "warning" ]; then
    exit 1
  else
    exit 2
  fi
fi
exit 0
