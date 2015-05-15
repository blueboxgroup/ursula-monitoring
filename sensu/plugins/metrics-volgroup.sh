#!/bin/bash

# #RED
SCHEME=$(hostname)
VOLGROUP=vg0

usage()
{
  cat <<EOF
usage: $0 options

This plugin shows disk usage of volume groups

OPTIONS:
   -h      Show this message
   -s      Metric naming scheme, text to prepend to cpu.usage (default: $SCHEME)
   -v      Volume group to check for.
EOF
}

while getopts "hs:v:" OPTION
  do
    case $OPTION in
      h)
        usage
        exit 1
        ;;
      s)
        SCHEME="$OPTARG"
        ;;
      v)
        VOLGROUP="$OPTARG"
        ;;
      ?)
        usage
        exit 1
        ;;
    esac
done

VG_METRICS=($(vgdisplay -C --noheadings --nosuffix --options vg_size,vg_free --separator=" " --units=B ${VOLGROUP}))

if [[ $? != "0" ]]; then
  echo "cannot query volume group: ${VOLGROUP}"
  exit 1
fi

VG_LVMS=$(lvdisplay -C --nosuffix  --separator=" " --noheading ${VOLGROUP} | wc -l)

DATE=$(date +%s)

echo "$SCHEME.lvm.vg.${VOLGROUP}.size ${VG_METRICS[0]} ${DATE}"
echo "$SCHEME.lvm.vg.${VOLGROUP}.free ${VG_METRICS[1]} ${DATE}"
echo "$SCHEME.lvm.vg.${VOLGROUP}.lvcount ${VG_LVMS} ${DATE}"
