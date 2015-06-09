#!/bin/bash

if lspci | grep RAID | grep -q -i 3ware; then
    sudo /etc/sensu/plugins/check_3ware_raid.py -b /usr/sbin/tw-cli
elif lspci | grep RAID | grep -q -i MegaRAID; then
    if type -p storcli64 storcli; then
      sudo /etc/sensu/plugins/check-storcli.pl
    else
      sudo /etc/sensu/plugins/check_megaraid_sas.pl -b /usr/sbin/megacli -o 63
    fi
fi;
