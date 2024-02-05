# returns a list of rofigen/bash-sourceable lines

import os, sys, re

DEBUG = True # spam stderr with useless stuff
TITLE = "Wrapwine Scanner (python)" # title used for dmenu

def debug(*message):
    if DEBUG:
        return stderr(*message)

def stderr(*message):
    print(*message, file=sys.stderr)

EXPAND_PATH_REGEX = re.compile(r"(?P<full>\${(?P<key>\w+)}|\$(?P<old_key>\w+))") # grabs "$ENV" or "${ENV}" from line
def expand_path(path, env_vars):
    regex = EXPAND_PATH_REGEX
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    matches = regex.match(path)
    if matches:
        gd = matches.groupdict()
        key = str()
        if gd["old_key"] is not None:
            stderr("WARN: avoid using '$VAR' assignments, this is not predictable - use '${VAR}' instead")
            key = gd["old_key"]
        else:
            key = gd["key"]

        if key in env_vars.keys():
            replacement_value = env_vars[key]
            path = path.replace(gd['full'], replacement_value)
            debug(f"successful replace of {gd['full']}: '{path}', replaced with '{replacement_value}'")
        else:
            debug(f"needs more expansion :(: {gd['full']}")

    return path

def expand_env_vars(env_vars):
    for (key, val) in env_vars.items():
        if debug:
            orig_val = val
            #debug(f"orig val: {val}")
        val = expand_path(val, env_vars)
        #debug(f"new val: {val}")
        if debug and val is not orig_val:
            debug(f"expand_env_vars, modified key '{key}' from '{orig_val}' to '{val}'")
        env_vars[key] = val
    return env_vars

REQUIRED_ENV_VARS = [
        "TITLE",
        "WINEPREFIX",
        "GAMEDIR",
        "FILENAME",
    ]

COMMAND = "wrapwine '{File}' --nobash"

def parse_bash_file(filename):
    errs = []
    found_env_var_regexes = []
    set_env_vars = {}
    skip = False
    base_title = str()
    with open(filename) as file:
        debug(f"\n - Scanning file '{filename}'")
        for line in file:
            #debug(f"line: {line}")
            # skip comment lines
            if line[0] == "#":
                continue

            # grab variable assignments
            variable_assignment_regex = re.compile(r"^(export )?(\w+?)=(.*)$") # FIXME: grabs comments from values e.g. beat-saber-mod-managers
            matches = variable_assignment_regex.match(line)
            if matches and matches.lastindex >= 2: # is a variable assignment
                key = matches.group(2)
                val = matches.group(3).strip('"')
                #debug(f"Setting '{key}' to: '{val}'")
                if key in set_env_vars:
                    stderr(f"WARN: Duplicate key '{key}' found")
                set_env_vars[key] = val

    # ensure any path env vars are expanded
    set_env_vars = expand_env_vars(set_env_vars)

    if "TITLE" not in set_env_vars:
        errs.append("Could not get base title")
        debug(f"err: set_env_vars: {set_env_vars}")
        skip = True
    else:
        base_title = set_env_vars["TITLE"]

    # check for (other) obligatory env vars
    debug(set_env_vars.keys())
    missing_required_env_vars = set(REQUIRED_ENV_VARS) - set(list(set_env_vars.keys()))
    if len(missing_required_env_vars) > 0:
        errs.append(f"Missing env vars: {missing_required_env_vars}")
        debug(f"err: missing env vars: {missing_required_env_vars}")
        skip = True

    wineprefix_path = str()
    if "WINEPREFIX" in set_env_vars:
        wineprefix_path = os.path.expandvars(set_env_vars["WINEPREFIX"]).rstrip('/')
        if not os.path.exists(wineprefix_path):
            errs.append(f"WINEPREFIX not found: '{wineprefix_path}'")
            skip = True
        elif not os.path.isdir(wineprefix_path):
            errs.append(f"WINEPREFIX '{wineprefix_path}' is not a dir")
            skip = True
    # else WINEPREFIX is missing but this is likely caught earlier

    # check for IGNORE keys
    if "IGNORE" in set_env_vars:
        # we don't want to set an error
        skip = True

    title = str()
    # prepend remoteness to title
    if wineprefix_path and os.path.isdir(wineprefix_path):
        if os.path.islink(wineprefix_path):
            debug(f"is symlink: {wineprefix_path}")
            title = "{Remote}: " + base_title
        else:
            debug(f"is not symlink: {wineprefix_path}")
            title = base_title 

        if "GAMEDIR" in set_env_vars:
            gamedir = set_env_vars["GAMEDIR"].rstrip('/')
            if not os.path.isdir(gamedir):
                gamedir = os.path.join(wineprefix_path, gamedir)
                if not os.path.isdir(gamedir):
                    errs.append(f"GAMEDIR not found: {gamedir}")
                    skip = True

            if "FILENAME" in set_env_vars:
                execfile = set_env_vars["FILENAME"]
                finalpath = os.path.join(gamedir, execfile)
                if not os.path.exists(finalpath): # not necessarily an issue
                    title = f"{title} (bad file?)"
                    debug(f"FILENAME not found: {finalpath}")

    # TODO: check ISODIR/ISOLOC

    if "ISODIR" in set_env_vars or "ISOLOC" in set_env_vars:
        errs.append(f"ISOLOC/ISODIR unimplemented")
        skip = True

    # ensure some sort of title
    if not title:
        title = base_title

    command = COMMAND.format(File=filename)

    return (title, command, errs if len(errs) > 0 else None, skip)

if (len(sys.argv) != 2):
    stderr(f"usage: {sys.argv[0]} /path/to/wrapwines")
    sys.exit(2)

debug('args:', sys.argv[1])

dirname = sys.argv[1]

if not os.path.isdir(dirname):
    stderr(f"Arg must be a directory!")
    sys.exit(2)

# OK, parse wrapwrines...

commands = []
for filename in os.listdir(dirname):
    f = os.path.join(dirname, filename)
    debug("file:", f)
    if not os.path.isfile(f):
        debug("skip")
        continue

    commands.append(parse_bash_file(f))

## parsing success, lets output..

# ..rofigen menu title
if TITLE:
    print(f'title="{TITLE}"')

commands.sort(key=lambda x: x[0].lower())

# ..rofigen menu entries
for (title, command, err, skip) in commands:
    if err and skip:
        stderr(f"ERROR: {', '.join(err)}, skipping '{title}'")
        continue
    elif err and len(err) > 0:
        stderr(f"WARN: '{title}' has errors but was passed through anyway: {','.join(err)}")
    elif skip:
        stderr(f"INFO: Skip set but no errors, skipping '{title}' (is IGNORE set?)")
        continue

    print(f"menu[\"{title}\"]=\"{command}\"")
