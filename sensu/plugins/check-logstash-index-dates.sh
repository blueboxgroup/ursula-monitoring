#!/usr/bin/env bash
#
# This runs on elk hosts.
# Checks to ensure there are no logstash indexes with a future date.
# Checks to ensure curator has deleted old indexes.
#

INDEX_MAX_AGE=$1
if [[ -z $INDEX_MAX_AGE ]]; then
    echo -e "USAGE: $0 INDEX_MAX_AGE\nERROR: Missing INDEX_MAX_AGE argument"
    exit 2
fi

declare -a ERR_MSGS

# joins elements of an array with the given character
function join_by { local IFS="$1"; shift; echo "$*"; }

# checks for indexes with future dates
function find_future_indexes {
    TODAY=$(date -I)
    count=0
    for index in $(curl -s localhost:9200/_cat/indices?v  | grep -P '\d\d\d\d.\d\d.\d\d' | awk '{print $3}' | sed 's/.*-//;s/\./-/g;s/ .*//' | sort -nk1); do
        if [[ $index > $TODAY ]]; then
            count=$(( $count + 1 ))
        fi
    done

    if [[ $count -gt 0 ]]; then
        ERR_MSGS+=("$count elasticsearch index(es) with future dates were found.")
    fi
}

# checks for old indexes that were not curated
function find_old_indexes {
    CUTOFF_DATE=`date --date="$(( $INDEX_MAX_AGE + 1 )) day ago" +%Y.%m.%d`

    count=0
    for i in $(curl -s 'localhost:9200/_cat/indices' | grep -E "[0-9]{4}.[0-9]{2}.[0-9]{2}" | awk '{print $3}' | sort -n); do
        if [[ ${i##*-} < $CUTOFF_DATE ]]; then
            count=$(( $count + 1 ))
        fi
    done

    if [[ $count -gt 0 ]]; then
        ERR_MSGS+=("$count $INDEX_PREFIX index(es) older than $INDEX_MAX_AGE days found.")
    fi
}

find_future_indexes
find_old_indexes

if [[ ${#ERR_MSGS[*]} -eq 0 ]]; then
    echo "OK: no indexes with future dates or that haven't been curated were found."
    exit 0
else
    join_by " "  "${ERR_MSGS[@]}"
    exit 2
fi
