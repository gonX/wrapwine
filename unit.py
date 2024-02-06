import os, sys, re
import env_parser, conf
from util import *

class Unit:
    REQUIRED_ENV_VARS = [
            "TITLE",
            "WINEPREFIX",
            "GAMEDIR",
            "FILENAME",
        ]

    def __init__(self, filename):
        self.errors = []
        self.skip = False
        self._filename = self._titlebase = filename
        self._filelines = self._read_file()
        self._vars = env_parser.EnvVars(self._filelines)
        if self._sanity_check():
            self._init_class_vars()
            self._verify()
            self._iso_check()

    def _sanity_check(self):
        fail = False
        for required_var in self.REQUIRED_ENV_VARS:
            if not self._vars.has_key(required_var):
                error = f"Missing key {required_var}"
                stderr(f"ERR: {error}")
                self.errors.append(error)
                self.skip = fail = True
        return not fail

    # checks that should be run iteratively, ie. if an earlier one fails, don't run later ones
    def _verify(self):
        commands = [ self._wineprefix_check,
            self._gamedir_check,
        ]
        for command in commands:
            if not command():
                stderr(f"ERR: Failed verification on {command.__name__}")
                return False
        return True

    def _filename_check(self):
        finalpath = os.path.join(self.gamedir, self.exename)
        return os.path.exists(finalpath)

    @staticmethod
    def _check_folder(folder):
        return os.path.isdir(folder)

    def _gamedir_check(self):
        rv = self._check_folder(self.gamedir)
        if not rv:
            wineprefix_added_path = os.path.join(self.wineprefix, self.gamedir)
            rv = self._check_folder(wineprefix_added_path)
            if rv:
                self.gamedir = wineprefix_added_path
            else:
                stderr("ERR: could not correctly determine gamedir path")
        return rv

    def _wineprefix_check(self):
        return self._check_folder(self.wineprefix)

    def _iso_check(self):
        # TODO: properly support ISODIR/ISOLOC
        var_keys = self._vars.get_keys()
        if "ISODIR" in var_keys or "ISOLOC" in var_keys:
            self.errors.append(f"ISOLOC/ISODIR unimplemented")
            self.skip = True
            return False
        return True

    def _init_class_vars(self):
        self._titlebase = self._vars.get_by_key("TITLE").value
        self.wineprefix = self._vars.get_by_key("WINEPREFIX").value.rstrip('/')
        self.gamedir    = self._vars.get_by_key("GAMEDIR").value.rstrip('/')
        self.exename    = self._vars.get_by_key("FILENAME").value
        self.skip       = self._vars.has_key("IGNORE")

    def _read_file(self):
        if not self._filename:
            raise "_filename should be instantiated first"

        debug(f"- Scanning file '{self._filename}'")
        with open(self._filename, 'r') as file:
            for line in file:
                yield line

    def get_basic_title(self):
        return self._titlebase

    def get_fancy_title(self):
        prepend = str()
        append  = str()
        if not self._vars.has_key("TITLE"):
            return self._titlebase
        title = self._titlebase

        if self.is_remote():
            prepend = prepend + "{Remote}: "

        if not self._filename_check():
            append = append + " (bad file?)"

        rv = title
        if prepend:
            rv = f"{prepend}{rv}"

        if append:
            rv = f"{rv}{append}"

        return rv

    def get_vars(self):
        return self._vars

    def get_source_file(self):
        return self._filename

    def get_command(self):
        return conf.COMMAND.format(File=self._filename)

    # return True/False whether WINEPREFIX is a link
    # TODO: follow link to see if it matches network paths (set in e.g. conf)
    def is_remote(self):
        return os.path.islink(self.wineprefix)
