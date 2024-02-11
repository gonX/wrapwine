import sys, os
import conf, unit

def debug(*message):
    if conf.DEBUG:
        return stderr(*message)

def stderr(*message):
    print(*message, file=sys.stderr)

def get_units(path):
    for filename in os.listdir(path):
        f = os.path.join(path, filename)
        yield unit.Unit(f)
