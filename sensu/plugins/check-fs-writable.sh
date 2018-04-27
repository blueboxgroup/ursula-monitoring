#!/bin/bash
# checks that all mounts listed in fstab are writeable

mount_status=0

for mount in $( findmnt -sno target | grep -v none ); do
  file="${mount}/.tmp-writable-check"
  trap '[[ -f "${file}" ]] && rm "${file}"' TERM EXIT

  if ! touch "$file" 2>/dev/null; then
    echo "FAIL - Could not create a file into '${mount}' !"
    ((mount_status++))
  fi
done

if [[ $mount_status == 0 ]]; then
  echo "OK - all fstab mounts are writable"
  exit 0
else
  echo "CRITICAL - '${mount_status}' mount(s) failing to write data"
  exit 2
fi
