#!/usr/bin/env bash

mydir="$(dirname "$0")"

if [ "$#" -eq 0 ]; then # no args, list everything
  python "${mydir}"/rofi.py
else # args, try to run application
  # must use coproc **and** redirect stdout/stderr otherwise rofi hangs
  coproc (python "${mydir}"/rofi.py $@ > /dev/null 2>&1)
fi
