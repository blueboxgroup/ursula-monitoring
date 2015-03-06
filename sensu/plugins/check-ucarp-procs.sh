#!/bin/bash

for IFACE in $(ifquery --list); do
  for VIP in $(ifquery ${IFACE} | awk '/^ucarp-vip:/ {print $2}'); do
    if ! ps -ef | grep '/usr/sbin/ucarp' | grep ${VIP} >/dev/null; then
      echo "no ucarp process is running for IP ${VIP}"
      exit 2
    fi
  done
done

echo "All interfaces configured with uCARP have running process"
