#!/bin/bash

HOST=$(hostname -s)
EXT=eth0.400

usage()
{
  cat <<EOF
usage: $0 options

This plugin shows the status of the external uCARP interface and the Neutron L3 router.

OPTIONS:
   -h      Show this message
   -e      External interface
   -z      Set sensu alert level, default is critical
EOF
}

while getopts "he:z:" OPTION
  do
    case $OPTION in
      h)
        usage
        exit 1
        ;;
      e)
        EXT="$OPTARG"
        ;;
      z)
        CRITICALITY="$OPTARG"
        ;;
      ?)
        usage
        exit 1
        ;;
    esac
done

EXTVIP=$(ifquery ${EXT} | awk '/^ucarp-vip:/ {print $2}')
CRITICALITY=${CRITICALITY:-critical}

if ip a | grep ${EXTVIP} >/dev/null; then
  EXTUCARP="owned"
fi

if neutron l3-agent-list-hosting-router default | grep $HOST >/dev/null; then
  L3="owned"
fi

if [ -n "$EXTUCARP" ] && [ -z "$L3" ]; then
  echo "uCARP interface is up, but $HOST does not own L3 router"
  if [ "$CRITICALITY" == "warning" ]; then
    exit 1
  else
    exit 2
  fi
fi

if [ -z "$EXTUCARP" ] && [ -n "$L3" ]; then
  echo "uCARP interface is down, but $HOST owns L3 router"
  if [ "$CRITICALITY" == "warning" ]; then
    exit 1
  else
    exit 2
  fi
fi

if [ -z "$EXTUCARP" ] && [ -z "$L3" ]; then
  echo "$HOST is not active controller.  No active uCARP interface, and no L3 router"
  exit 0
fi

if [ -n "$EXTUCARP" ] && [ -n "$L3" ]; then
  echo "uCARP interface is up and $HOST owns L3 router"
  exit 0
fi
