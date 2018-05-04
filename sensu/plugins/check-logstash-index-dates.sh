#!/usr/bin/env bash
#
# This runs on elk hosts.
# Checks to ensure there are no logstash indexes with a future date.
#

TODAY=$(date -I)

let "count=0"
for index in $(curl -s localhost:9200/_cat/indices?v  | grep -P '\d\d\d\d.\d\d.\d\d' | awk '{print $3}' | sed 's/.*-//;s/\./-/g;s/ .*//' | sort -nk1); do
    if [[ $index > $TODAY ]]; then
        let "count++"
    fi
done

if [[ $count -gt 0 ]]; then
    echo "CRITICAL: $count elasticsearch index(es) with future dates were found."
    exit 2
fi

echo "OK: 0 elasticsearch indexes with future dates."
