#!/bin/bash

# #RED
SCHEME=$(hostname).nova.oversubscription

usage()
{
  cat <<EOF
usage: $0 options

This plugin shows CPU / Mem oversubscription ratios for Nova

OPTIONS:
   -h      Show this message
   -s      Metric naming scheme, text to prepend to cpu.usage (default: $SCHEME)
EOF
}

while getopts "hs:" OPTION
  do
    case $OPTION in
      h)
        usage
        exit 1
        ;;
      s)
        SCHEME="$OPTARG"
        ;;
      ?)
        usage
        exit 1
        ;;
    esac
done

CPU=$(grep cpu_allocation_ratio /etc/nova/nova.conf | awk -F= '{ print $2}')
RAM=$(grep ram_allocation_ratio /etc/nova/nova.conf | awk -F= '{ print $2}')

echo "$SCHEME.cpu $CPU `date +%s`"
echo "$SCHEME.ram $RAM `date +%s`"
