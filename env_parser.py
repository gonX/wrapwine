import re, os
from util import *

class EnvVar:
    """Class for parsing a BASH-style environment variable"""
    EXPAND_PATH_REGEX = re.compile(r"(?P<full>\${(?P<key>\w+)}|\$(?P<old_key>\w+))") # grabs "$ENV" or "${ENV}" from line
    VARIABLE_ASSIGNMENT_REGEX = re.compile(r"^(export )?(\w+?)=(.*)$") # FIXME: grabs comments from values e.g. beat-saber-mod-managers

    def __init__(self, line):
        self.line = line
        self.parseline()

    # expand all variables inside of value
    def expand(self, env_vars):
        if not self.key or not self.value:
            raise Exception("Missing key and/or value")
        self._simple_expand()
        expand_value = self.should_expand()
        if expand_value:
            self._complex_expand(env_vars)

    # use python's builtin functions to expand path value
    def _simple_expand(self):
        self.value = os.path.expanduser(self.value)
        self.value = os.path.expandvars(self.value)

    # expand variables from provided dictionary
    def _complex_expand(self, env_vars):
        gd = self.should_expand().groupdict()
        key = str()
        if gd["old_key"] is not None:
            stderr("WARN: avoid using '$VAR' assignments, this is not predictable - use '${VAR}' instead")
            key = gd["old_key"]
        else:
            key = gd["key"]

        if key in [x.key for x in env_vars]:
            replacement = next(filter(lambda x: x.key == key, env_vars))
            self.value = self.value.replace(gd['full'], replacement.value)

    # returns True if self.value still contains unexpanded variables
    def should_expand(self):
        if not self.value:
            raise "value is unset, unable to determine expand"

        return self.EXPAND_PATH_REGEX.match(self.value)

    # set key and value based on line
    def parseline(self):
        # grab variable assignments
        matches = self.VARIABLE_ASSIGNMENT_REGEX.match(self.line)
        if matches and matches.lastindex >= 2: # is a variable assignment
            self.key = matches.group(2)
            self.value = matches.group(3).strip('"')

class EnvVars:
    def __init__(self, lines):
        self.env_vars = []
        for line in lines:
            if line[0] == "#": # is comment
                continue

            if EnvVar.VARIABLE_ASSIGNMENT_REGEX.match(line):
                env_var = EnvVar(line)
                if env_var.key in self.get_keys():
                    stderr(f"ERROR: Duplicate key '{env_var.key}' found")
                    raise ":("

                self.env_vars.append(env_var)
        self.expand()

    def __iter__(self):
        self._iter = -1
        self._iter_max = len(self.env_vars)
        return self

    def __next__(self):
        self._iter += 1
        if self._iter >= self._iter_max:
            raise StopIteration
        return self.env_vars[self._iter]

    def has_key(self, key):
        keys = self.get_keys()
        return key in keys

    def get_by_key(self, key):
        return next(filter(lambda x: x.key == key, self.env_vars), None)

    def get_keys(self):
        return [ var.key for var in self.env_vars ]

    # expand all env vars
    def expand(self):
        MAX_LOOPS = 10 # very unlikely this actually occurs unless there's a bug
        loop = 0
        while any(x.should_expand() for x in self.env_vars):
            loop = loop + 1
            if loop > MAX_LOOPS:
                raise Exception("Looped longer than expected")
            for env_var in self.env_vars:
                if env_var.should_expand():
                    env_var.expand(self.env_vars)
        #debug(f"Successfully expanded all {len(self.env_vars)} env vars")
