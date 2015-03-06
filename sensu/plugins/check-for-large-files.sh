#!/bin/bash
#
# Check how many files are larger than X in DIR.
#

# get arguments
while getopts 'w:c:d:s:h' OPT; do
  case $OPT in
    w)  WARN=$OPTARG;;
    c)  CRIT=$OPTARG;;
    h)  hlp="yes";;
    d)  DIR=$OPTARG;;
    s)  SIZE=$OPTARG;;
    *)  unknown="yes";;
  esac
done

# usage
HELP="
    Tests how many files are larger than a given size in a directory
    usage: $0 [ -w value -c value -p -h ]

        -w --> Warning < value
        -c --> Critical < value
        -d --> Directory to Check
        -s --> filesize threshhold
        -h --> print this help screen
"

if [ "$hlp" = "yes" ]; then
  echo "$HELP"
  exit 0
fi

WARN=${WARN:=3}
CRIT=${CRIT:=10}
DIR=${DIR:=/var/log}
SIZE=${SIZE:=1048576}

NUM_FILES=`find ${DIR} -type f -size +${SIZE} | wc -l`

if (( $NUM_FILES == 1)); then
  FILE=file
else
  FILE=files
fi

output="$NUM_FILES $FILE bigger than ${SIZE} in ${DIR}"

if (( $NUM_FILES >= $CRIT )); then
  echo "CRITICAL - $output"
  exit 2
elif (( $NUM_FILES >= $WARN )); then
  echo "WARN - $output"
  exit 1
else
  echo "OK - $output"
  exit 0
fi
