import os, sys, subprocess, re
from pathlib import Path
import conf, unit
from util import *

# path to wrapwines
WRAPWINE_PATH = os.path.expanduser("~/.wrapwines")

class Rofi:
    # title of rofi prompt if running in rofi
    ROFI_PROMPT = conf.TITLE

    # any variable that ROFI sets
    ROFI_PRESENCE_ENV_VAR = "ROFI_RETV"

    # add markup for rofi
    ENHANCE_ROFI = True if ROFI_PRESENCE_ENV_VAR in os.environ else False

    MINIMUM_SUPPORTED_ROFI_VERSION = "1.7.5"

    VERSION_REGEX = re.compile('^Version: (\d\.\d\.\d)$')
    VERSION_COMMAND = [ "/usr/bin/rofi", "-version" ]

    # key is mode_OPTION or row_OPTION, value is minimum rofi version supported
    COMPATIBLE_ROFI_OPTS_TO_VERSION = {
            "row_display": "1.7.6", # display string (and use original title as search string)
            "row_urgent": "1.7.6", # highlight row - earlier versions can use old dmenu syntax in mode option
            # 1.7.5 or earlier:
            "row_nonselectable": "1.7.5" # prevents rofi from submitting this as an option

            # currently unused:

            #"row_icon": "1.7.5"
            #"row_meta": "1.7.5" # invisible search terms
            #"row_info": "1.7.5" # backref variable, currently unused

            # all currently used mode options are supported in 1.7.5 beyond

            #"mode_prompt": "1.7.5",
            #"mode_message": "1.7.5",
            #"mode_markup-rows": "1.7.5",
            #"mode_urgent": "1.7.5",
            #"mode_active": "1.7.5",
            #"mode_delim": "1.7.5",
            #"mode_no-custom": "1.7.5",
            #"mode_use-hot-keys": "1.7.5",
            #"mode_keep-selection": "1.7.5",
            #"mode_new-selection": "1.7.5",
            #"mode_data": "1.7.5",
            #"mode_theme": "1.7.5",
        }

    def __init__(self, wrapwine_path):
        self.rofi_version = self._get_rofi_version()
        if not os.path.isdir(wrapwine_path):
            raise Exception("wrapwine_path must be a directory")
        self.wrapwine_path = wrapwine_path
        self.units = list(get_units(self.wrapwine_path))
        self.units.sort(key=lambda x: x.get_fancy_title().lower())

    # where is "mode" or "row"
    def is_opt_supported(self, where, option):
        if where == "mode":
            return self.rofi_version >= self.MINIMUM_SUPPORTED_ROFI_VERSION # all are supported in 1.7.5 (or earlier) and beyond

        key = f"{where}_{option}"
        if key not in self.COMPATIBLE_ROFI_OPTS_TO_VERSION:
            raise Exception(f"Key '{key}' not supported yet")
        val = self.COMPATIBLE_ROFI_OPTS_TO_VERSION[key]

        return self.rofi_version >= val

    def is_row_opt_supported(self, option):
        return self.is_opt_supported("row", option)

    def is_mode_opt_supported(self, option):
        return self.is_opt_supported("mode", option)

    def _get_rofi_version(self):
        result = subprocess.run(self.VERSION_COMMAND, capture_output=True, text=True)
        match = self.VERSION_REGEX.match(result.stdout)
        if match:
            return match.group(1)
        else:
            raise Exception("Could not determine rofi version")

    # return a string of supported desired options that can be appended to a rofi row
    def get_title_options(self, opts):
        rv = "\0"
        sep = chr(0x1f)
        for opt in opts:
            if not self.is_row_opt_supported(opt):
                debug(f"Skipping unsupported option '{opt}'")
                continue
            rv = rv + opt + sep + opts[opt] + sep
        return rv[:-len(sep)]

    # return a row for use in rofi, optionally marked up
    def get_rofi_title(self, unit):
        opts = {}

        if not self.is_row_opt_supported("display"):
            title = unit.get_fancy_title()
        else:
            title = unit.get_basic_title()
            opts["display"] = '"' + unit.get_fancy_title() + '"'

        if not unit.is_usable():
            opts["nonselectable"] = "true"
            opts["urgent"] = "true"

        return title + self.get_title_options(opts)

    # prints the fancy title of all units in order
    def output_titles(self):
        for unit in self.units:
            if self.ENHANCE_ROFI:
                print(f"{self.get_rofi_title(unit)}")
            else:
                print(f"{unit.get_fancy_title()}")

    # launches unit based on fancy title
    def launch_title(self, argv_fancy_title):
        fancy_title = ' '.join(argv_fancy_title[1:])
        target = next(filter(lambda x: x.get_fancy_title() == fancy_title, self.units), None)
        if target is None:
            stderr(f"ERROR! Could not find a title matching '{fancy_title}'")
            sys.exit(1)

        debug(f"Launching program title '{unit.get_basic_title()}'")
        return target.launch()

    # print rofi mode option
    def print_rofi_option(self, key, value):
        if self.is_mode_opt_supported(key):
            print('\0' + key + chr(0x1f) + value)
        else:
            debug(f"Skipping unsupported mode key '{key}'")

    # print relevant rofi mode options
    def output_rofi_enhancements(self):
        if not self.ENHANCE_ROFI:
            return False

        units = self.units

        self.print_rofi_option("prompt", self.ROFI_PROMPT)
        self.print_rofi_option("no-custom", "true")
        if self.rofi_version < '1.7.6': # first version that supports row marking
            bad_units = [ str(units.index(u)) for u in units if not u.is_usable() ]
            self.print_rofi_option("urgent", ','.join(bad_units))
        return True

if __name__ == "__main__":
    rofi = Rofi(WRAPWINE_PATH)
    # no args
    if len(sys.argv) == 1:
        rofi.output_rofi_enhancements()
        rofi.output_titles()
    # yes args
    elif len(sys.argv) >= 1:
        rofi.launch_title(sys.argv)


