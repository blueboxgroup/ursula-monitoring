#!/bin/bash
#
# only run command on node with the floating ip

# #RED
while getopts 'i:c:h' OPT; do
  case $OPT in
    i)  IP=$OPTARG;;
    c)  COMMAND=$OPTARG;;
    h)  hlp="yes";;
  esac
done

# usage
HELP="
    usage: $0 [ -i IP -c COMMAND -h ]
        -i --> only run command on node with the floating ip
        -c --> command
        -h --> print this help screen
"

if [ "$hlp" = "yes" ]; then
  echo "$HELP"
  exit 0
fi

if ip a | grep "${IP}" > /dev/null 2>&1; then
  ${COMMAND}
fi;
