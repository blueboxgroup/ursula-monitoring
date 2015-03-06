#!/bin/bash
#
# Checks if same file is opened by multiple /dev/nbdX devices

while getopts 'w:c:h' OPT; do
  case $OPT in
    c)  CRIT=$OPTARG;;
    h)  hlp="yes";;
    *)  unknown="yes";;
  esac
done

# usage
HELP="
    usage: $0 [ -w value -c value -p -h ]

        -c --> Critical < value
        -h --> print this help screen
"

if [ "$hlp" = "yes" ]; then
  echo "$HELP"
  exit 0
fi

CRIT=${CRIT:=1}

NO_NBD=`ps h $(pgrep qemu-nbd) | awk '{ print $(NF) }' | uniq -d | wc -l`

output="$NO_NBD files open by multiple /dev/nbdX"

if (( $NO_NBD >= 1 )); then
  echo "CRITICAL - $output"
  exit 2
else
  echo "OK - $output"
  exit 0
fi
