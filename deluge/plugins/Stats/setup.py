# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Ian Martin <ianmartin@cantab.net>
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from setuptools import find_packages, setup

__plugin_name__ = 'Stats'
__author__ = 'Ian Martin'
__author_email__ = 'ianmartin@cantab.net'
__version__ = '0.4'
__url__ = 'http://deluge-torrent.org'
__license__ = 'GPLv3'
__description__ = 'Display stats graphs'
__long_description__ = """
Records lots of extra stats
and produces time series
graphs"""
__pkg_data__ = {'deluge_' + __plugin_name__.lower(): ['template/*', 'data/*']}

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
