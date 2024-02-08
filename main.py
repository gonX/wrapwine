# unsupported, will break on changes
# supposed to be used with rofigen, not sure how to actually apply this without using eval which is ugly

import os, sys
import conf, unit
from util import *

if __name__ == "__main__":
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

        commands.append(unit.Unit(f))

    ## parsing success, lets output..

    # ..rofigen menu title
    if conf.TITLE:
        print(f'title="{conf.TITLE}"')
    else:
        stderr("WARN: Title was unset, this is probably not intentional")

    commands.sort(key=lambda x: x.get_fancy_title().lower())

    # ..rofigen menu entries
    for command in commands:
        title = command.get_fancy_title()
        comm = command.get_command()
        if command.errors and command.skip:
            stderr(f"ERROR: {', '.join(command.errors)}, skipping '{title}'")
            continue
        elif command.errors and len(command.errors) > 0:
            stderr(f"WARN: '{title}' has errors but was passed through anyway: {','.join(err)}")
        elif command.skip:
            stderr(f"INFO: Skip set but no errors, skipping '{title}' (is IGNORE set?)")
            continue

        print(f"menu[\"{title}\"]=\"{comm}\"")
