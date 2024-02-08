#!/usr/bin/env bash

mydir="$(dirname "$0")"
if [ "$#" -eq 0 ]; then
  python "${mydir}"/rofi.py
else
  coproc (python "${mydir}"/rofi.py $@ > /dev/null 2>&1)
fi
