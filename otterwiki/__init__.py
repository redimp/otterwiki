#!/usr/bin/env python

import os
import sys
from .version import __version__


def fatal_error(msg):
    print("Error: {}".format(msg), file=sys.stderr)
    sys.exit(1)


# vim: set et ts=8 sts=4 sw=4 ai:
