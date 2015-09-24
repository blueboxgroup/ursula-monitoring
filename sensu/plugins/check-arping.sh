#!/usr/bin/env bash
# Run arping in duplicate address detection mode for specified destination

while getopts 'I:d:' OPT; do
  case "$OPT" in
    I) interface="$OPTARG";;
    d) destination="$OPTARG";;
  esac
done

if [[ -z "$interface" || -z "$destination" ]]; then
  echo "Usage: $0 -I device -d destination"
  exit 1
fi

output=$(arping -D -I $interface -c 2 $destination)

if [ $? -eq 0 ]; then
  echo "ERROR: Duplicate address detected for $destination"
  echo "$output"
  exit 2
else
  echo "OK: Reply received for $destination"
  exit 0
fi
