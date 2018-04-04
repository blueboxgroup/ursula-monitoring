#!/usr/bin/env bash
#
# This tests that both filebeat and logstash-forwarder can connect to the
# target host:port specified in their respective configuration files.
#.

MSG=""
RC=0

check_port () {
    # some input validation
    if [[ $# -ne 2 ]]; then
        echo "expect 2 args, name and file, only got $# arg."
        exit 2
    elif ! [[ $1 == "filebeat" || $1 == "logstash-forwarder" ]]; then
        echo "I don't recognize '$1'. Only 'filebeat' and 'logstash-forwarder' supported"
        exit 2
    elif ! [[ $2 == "/etc/filebeat/filebeat.yml" || $2 == "/etc/logstash-forwarder.d/main.conf" ]]; then
        echo "unexpected config file: $2"
        exit 2
    fi

    NAME="$1"
    FILE="$2"

    if test -f $FILE; then
        HOST=$(grep -P 'logs.*:\d' $FILE | sed 's/.*"logs/logs/;s/".*//' | cut -d: -f1)
        PORT=$(grep -P 'logs.*:\d' $FILE | sed 's/.*"logs/logs/;s/".*//' | cut -d: -f2)
        nc -w3 -zv $HOST $PORT 2>/dev/null
        if [[ $? -eq 0 ]]; then
            MSG="$MSG $NAME connection to $HOST:$PORT OK."
        else
            RC=2
            MSG="$MSG $NAME connection to $HOST:$PORT FAIL."
        fi
    fi
}

check_port filebeat           /etc/filebeat/filebeat.yml
check_port logstash-forwarder /etc/logstash-forwarder.d/main.conf

echo $MSG
exit $RC
