#!/bin/bash

if lspci | grep RAID | grep -i 3ware >> /dev/null; then
    sudo /etc/sensu/plugins/check_3ware_raid.py -b /usr/sbin/tw-cli
elif lspci | grep RAID | grep -i "MegaRAID" >> /dev/null; then
    sudo /etc/sensu/plugins/check_megaraid_sas.pl -b /usr/sbin/megacli
fi;
