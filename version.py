# -*- coding: utf-8 -*-
# Authors: Douglas Creager <dcreager@dcreager.net>
#          Calum Lind <calumlind@gmail.com>
#
# This file is placed into the public domain.
#
# Calculates the current version number by first checking output of “git describe”,
# modified to conform to PEP 386 versioning scheme.  If “git describe” fails
# (likely due to using release tarball rather than git working copy), then fall
# back on reading the contents of the RELEASE-VERSION file.
#
# Usage: Import in setup.py, and use result of get_version() as package version:
#
# from version import *
#
# setup(
#     ...
#     version=get_version(),
#     ...
# )
#
# Script will automatically update the RELEASE-VERSION file, if needed.
# Note that  RELEASE-VERSION file should *not* be checked into git; please add
# it to your top-level .gitignore file.
#
# You'll probably want to distribute the RELEASE-VERSION file in your
# sdist tarballs; to do this, just create a MANIFEST.in file that
# contains the following line:
#
#   include RELEASE-VERSION
#

__all__ = ("get_version")

from subprocess import Popen, PIPE
VERSION_FILE = "RELEASE-VERSION"


def call_git_describe(prefix="", suffix=""):
    cmd = "git describe --tags --match %s[0-9]*" % prefix
    try:
        version = Popen(cmd.split(), stdout=PIPE).communicate()[0]
        version = version.strip().replace(prefix, "")
        if "-" in version:
            version = ".dev".join(version.replace(suffix, "").split("-")[:2])
        return version
    except:
        return None


def get_version(prefix="", suffix=""):
    try:
        with open(VERSION_FILE, "r") as f:
            release_version = f.readline().strip()
    except:
        release_version = None

    version = call_git_describe(prefix, suffix)

    if version is None:
        version = release_version
    if version is None:
        raise ValueError("Cannot find the version number!")

    if version != release_version:
        with open(VERSION_FILE, "w") as f:
            f.write("%s\n" % version)

    return version

if __name__ == "__main__":
    print get_version(prefix="deluge-", suffix=".dev0")
