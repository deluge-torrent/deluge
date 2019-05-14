# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from setuptools import find_packages, setup

__plugin_name__ = 'Extractor'
__author__ = 'Andrew Resch'
__author_email__ = 'andrewresch@gmail.com'
__version__ = '0.7'
__url__ = 'http://deluge-torrent.org'
__license__ = 'GPLv3'
__description__ = 'Extract files upon torrent completion'
__long_description__ = """
Extract files upon torrent completion

Supports: .rar, .tar, .zip, .7z .tar.gz, .tgz, .tar.bz2, .tbz .tar.lzma, .tlz, .tar.xz, .txz

Windows support: .rar, .zip, .tar, .7z, .xz, .lzma
( Requires 7-zip installed: http://www.7-zip.org/ )

Note: Will not extract with 'Move Completed' enabled
"""
__pkg_data__ = {'deluge_' + __plugin_name__.lower(): ['data/*']}

setup(
    name=__plugin_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    long_description=__long_description__ if __long_description__ else __description__,
    packages=find_packages(),
    package_data=__pkg_data__,
    entry_points="""
    [deluge.plugin.core]
    %s = deluge_%s:CorePlugin
    [deluge.plugin.gtk3ui]
    %s = deluge_%s:GtkUIPlugin
    [deluge.plugin.web]
    %s = deluge_%s:WebUIPlugin
    """
    % ((__plugin_name__, __plugin_name__.lower()) * 3),
)
