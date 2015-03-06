#!/bin/bash
#
# Check how many /dev/nbdX are in use.

while getopts 'w:c:h' OPT; do
  case $OPT in
    w)  WARN=$OPTARG;;
    c)  CRIT=$OPTARG;;
    h)  hlp="yes";;
    *)  unknown="yes";;
  esac
done

# usage
HELP="
    usage: $0 [ -w value -c value -p -h ]

        -w --> Warning < value
        -c --> Critical < value
        -h --> print this help screen
"

if [ "$hlp" = "yes" ]; then
  echo "$HELP"
  exit 0
fi

WARN=${WARN:=5}
CRIT=${CRIT:=10}

NO_NBD=`ls /sys/block/nbd*/pid | wc -l`

output="$NO_NBD nbd devices in use."

if (( $NO_NBD >= $CRIT )); then
  echo "CRITICAL - $output"
  exit 2
elif (( $NO_NBD >= $WARN )); then
  echo "WARNING - $output"
  exit 1
else
  echo "OK - $output"
  exit 0
fi
