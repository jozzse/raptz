

import os

locked = False
progs = {}

def register(prog):
        """ Register usage of program """
        if locked == True:
                print("Trying to get %s when locked" % prog)
                return False
        locations = os.environ.get("PATH").split(os.pathsep)
        for loc in locations:
                c = os.path.join(loc, prog)
                if os.path.isfile(c):
                        progs[prog] = c
                        return True
        print("Could not find '%s' in path." % prog)
        exit(0)

def lock():
        locked=True


def get(prog):
        return progs[prog]
