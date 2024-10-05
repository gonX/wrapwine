# example usage: python file.py /path/to/wrapwine/script

import sys
import unit

file_path = sys.argv[1]

target = unit.Unit(file_path)

if not target:
  print(f"Invalid unit {sys.argv}")
  sys.exit(1)

target.launch()
