#!/bin/bash
set -e
if nova-manage service list | tail -n +2 | grep XXX; then
  echo "a nova service is down"
  exit 2
fi
exit 0
