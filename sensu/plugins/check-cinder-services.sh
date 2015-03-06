#!/bin/bash
set -e
if cinder-manage service list | tail -n +2 | grep XXX; then
  echo "a cinder service is down"
  exit 2
fi
exit 0
