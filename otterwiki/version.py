#!/usr/bin/env python

# version_onfo managed by tbump
version_info = (2, 3, 0, "")

# build version string from version_info
__version__ = f"{version_info[0]}.{version_info[1]}.{version_info[2]}" + \
        (f"-{version_info[3]}" if len(version_info[3])>0 else "")

# vim: set et ts=8 sts=4 sw=4 ai:
