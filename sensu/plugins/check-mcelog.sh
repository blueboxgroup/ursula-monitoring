#!/bin/bash
# Queries the running mcelog daemon for accumulated errors.
# by Ulysses Kanigel

trap 'exit 1' ERR
if mcelog --client | grep total | grep -v "0 total"; then
  echo "mcelog reports memory errors"
  exit 2
fi
exit 0
