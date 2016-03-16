#!/bin/bash

while getopts 'z:' OPT; do
  case $OPT in
    z)  CRITICALITY=$OPTARG;;
  esac
done

CRITICALITY=${CRITICALITY:-critical}

for IFACE in $(ifquery --list); do
  for VIP in $(ifquery ${IFACE} | awk '/^ucarp-vip:/ {print $2}'); do
    if ! ps -ef | grep '/usr/sbin/ucarp' | grep ${VIP} >/dev/null; then
      echo "no ucarp process is running for IP ${VIP}"
      if [ "$CRITICALITY" == "warning" ]; then
        exit 1
      else
        exit 2
      fi
    fi
  done
done

echo "All interfaces configured with uCARP have running process"
