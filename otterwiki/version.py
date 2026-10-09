#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

# Keep the format of this file stable, others rely on it:
# - tbump rewrites the version_info tuple below
# - the Makefile exec()s this file to read __version__
# - pyproject.toml reads otterwiki.version.__version__
# - users read `from otterwiki import __version__` (see #586)
#
# version_info managed by tbump
version_info = (2, 25, 1, "")

# build version string from version_info
__version__ = f"{version_info[0]}.{version_info[1]}.{version_info[2]}" + (
    f"-{version_info[3]}" if len(version_info[3]) > 0 else ""
)
