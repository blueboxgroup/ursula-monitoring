#!/usr/bin/env bash

if [[ -n $1 ]]; then
    export http_proxy=$1
fi

if ! { apt-get update 2>&1 || echo "E: update failed"; } | grep -q '^[WE]:'; then
    echo "apt cache update successsful"
    exit 0
else
    echo "apt cache update failed"
    exit 2
fi
