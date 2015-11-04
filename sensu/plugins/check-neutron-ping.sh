#!/bin/bash

NS=$(ip netns list | grep qrouter)
IP=8.8.8.8

usage()
{
  cat <<EOF
usage: $0 options

This plugin confirms that the Neutron router can communicate externally.

OPTIONS:
   -h      Show this message
EOF
}

while getopts "he:" OPTION
  do
    case $OPTION in
      n)
        NS="$OPTARG"
        ;;
      ?)
        usage
        exit 1
        ;;
    esac
done

if [ -z "$NS" ]; then
  echo "Not active controller"
  exit 0
fi

if ip netns exec $NS ping -c 4 $IP; then
  echo "Neutron router can reach $IP"
  exit 0
else
  echo "Neutron router cannot reach $IP"
  exit 2
fi
