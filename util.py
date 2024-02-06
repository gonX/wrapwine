import sys
import conf

def debug(*message):
    if conf.DEBUG:
        return stderr(*message)

def stderr(*message):
    print(*message, file=sys.stderr)
