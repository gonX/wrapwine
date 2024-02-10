import os, sys, subprocess
from pathlib import Path
import conf, unit
from util import *

WRAPWINE_PATH = os.path.expanduser("~/.wrapwines")
ENHANCE_ROFI = True # set title etc
ROFI_PROMPT = conf.TITLE

def get_units():
    for filename in os.listdir(WRAPWINE_PATH):
        f = os.path.join(WRAPWINE_PATH, filename)
        yield unit.Unit(f)

def get_title_options(opts):
    rv = "\0"
    for opt in opts:
        debug(opt)
        rv = rv + opt + chr(0x1f) + opts[opt]
    return rv

def get_title_as_unselectable(title):
    arg = { "nonselectable": "true" }
    title_opts = get_title_options(arg)
    debug(f"setting title {title} as unselectable")
    return title + title_opts

def output_titles():
    units = list(get_units())

    units.sort(key=lambda x: x.get_fancy_title().lower())

    for unit in units:
        title = unit.get_fancy_title()
        if not unit.is_usable():
            print(f"{get_title_as_unselectable(title)}")
        else:
            print(f"{title}")

def launch_title(argv_fancy_title):
    fancy_title = ' '.join(argv_fancy_title[1:])
    target = next(filter(lambda x: x.get_fancy_title() == fancy_title, get_units()), None)
    if target is None:
        stderr(f"ERROR! Could not find a title matching '{fancy_title}'")
        sys.exit(1)
    debug(f"Launching program title '{target.get_basic_title()}'")

    # new
    target.launch()

    # old (passing off to wrapwine shell script):
    #command = target.get_command()
    #debug(f"command: {command}")
    #subprocess.Popen(command)

def print_rofi_option(key, value):
    print('\0' + key + chr(0x1f) + value + '\n')

def output_rofi_enhancements():
    if ROFI_PROMPT:
        print_rofi_option("prompt", ROFI_PROMPT)
    print_rofi_option("no-custom", "true")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        if ENHANCE_ROFI:
            output_rofi_enhancements()
        output_titles()
    elif len(sys.argv) >= 1:
        launch_title(sys.argv)


