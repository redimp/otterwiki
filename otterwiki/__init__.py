#!/usr/bin/env python

import sys
from .version import __version__

__all__ = ["fatal_error"]


def fatal_error(msg):
    print("Error: {}".format(msg), file=sys.stderr)
    sys.exit(1)


# vim: set et ts=8 sts=4 sw=4 ai:
