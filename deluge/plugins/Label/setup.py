# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from setuptools import find_packages, setup

__plugin_name__ = 'Label'
__author__ = 'Martijn Voncken'
__author_email__ = 'mvoncken@gmail.com'
__version__ = '0.3'
__url__ = 'http://deluge-torrent.org'
__license__ = 'GPLv3'
__description__ = 'Allows labels to be assigned to torrents'
__long_description__ = """
Allows labels to be assigned to torrents

Also offers filters on state, tracker and keywords
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
    long_description=__long_description__,
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
