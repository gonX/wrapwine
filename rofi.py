import os, sys, subprocess
from pathlib import Path
import conf, unit
from util import *

WRAPWINE_PATH = os.path.expanduser("~/.wrapwines")

def get_units():
    for filename in os.listdir(WRAPWINE_PATH):
        f = os.path.join(WRAPWINE_PATH, filename)
        yield unit.Unit(f)

def output_titles():
    titles = []
    for u in get_units():
        titles.append(u.get_fancy_title())

    titles.sort(key=lambda x: x.lower())
    newline = '\n'
    print(f"{newline.join(titles)}")

def launch_title(argv_fancy_title):
    fancy_title = ' '.join(argv_fancy_title[1:])
    target = next(filter(lambda x: x.get_fancy_title() == fancy_title, get_units()), None)
    if target is None:
        stderr(f"ERROR! Could not find a title matching '{fancy_title}'")
        sys.exit(1)
    debug(f"Launching program title '{target.get_basic_title()}'")

    command = target.get_command()
    debug(f"command: {command}")
    subprocess.Popen(command)
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        output_titles()
    elif len(sys.argv) >= 1:
        launch_title(sys.argv)


