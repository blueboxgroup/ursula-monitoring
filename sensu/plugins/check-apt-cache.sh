#!/usr/bin/env bash

# This checks that the apt cache has been updated recently.
# It relies on the periodic cron job that touches FILE after a successful run.

# the file that is touched by cron job on successful apt cache update
FILE=/var/lib/apt/update-cache-success

# arguments passed in for the warning/critical threshold in hours
WARNING_HOURS=$1
CRITICAL_HOURS=$2

if [ $# -ne 2 ]; then
    echo "usage: $0 WARNINGHOURS CRITICALHOURS"
    exit 3
fi

if ! [[ -f $FILE ]]; then
    echo "status file missing: $FILE"
    exit 3
fi

HOURS_SINCE_UPDATE=`echo $(( ($(date +%s) - $(date +%s -r "$FILE"))/60/60))`
MINUTES_SINCE_UPDATE=`echo $(( ($(date +%s) - $(date +%s -r "$FILE"))/60))`

if [[ $HOURS_SINCE_UPDATE -gt $WARNING_HOURS ]]; then
    echo "WARNING: stale apt cache, $HOURS_SINCE_UPDATE hours old."
    exit 1
elif [[ $HOURS_SINCE_UPDATE -gt $CRITICAL_HOURS ]]; then
    echo "CRITICAL: stale apt cache, $HOURS_SINCE_UPDATE hours old."
    exit 2
fi

echo "OK: last apt cache update was ${HOURS_SINCE_UPDATE}h (${MINUTES_SINCE_UPDATE}m) ago"
exit 0
