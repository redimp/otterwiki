#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

# version_onfo managed by tbump
version_info = (2, 17, 2, "")

# build version string from version_info
__version__ = f"{version_info[0]}.{version_info[1]}.{version_info[2]}" + (
    f"-{version_info[3]}" if len(version_info[3]) > 0 else ""
)
