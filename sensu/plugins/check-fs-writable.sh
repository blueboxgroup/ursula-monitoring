#!/bin/bash
# checks that all mounts listed in fstab are writeable

mount_status=0

for mount in $( findmnt -sno target | grep -v none ); do
  if [[ ! -d $mount ]]; then
    echo "FAIL - '${mount}' found in fstab, but not mounted!"
    ((mount_status++))
  else
    file="${mount}/.tmp-writeable-check"
    trap '[[ -f "${file}" ]] && rm "${file}"' TERM EXIT

    if ! touch "$file" 2>/dev/null; then
      echo "FAIL - Could not create a file into '${mount}' !"
      ((mount_status++))
    fi
  fi
done

if [[ $mount_status == 0 ]]; then
  echo "OK - all fstab mounts are writable"
  exit 0
else
  echo "CRITICAL - '${mount_status}' mount(s) failing to write data"
  exit 2
fi
