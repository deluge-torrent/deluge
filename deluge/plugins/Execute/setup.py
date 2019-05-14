# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from setuptools import find_packages, setup

__plugin_name__ = 'Execute'
__author__ = 'Damien Churchill'
__author_email__ = 'damoxc@gmail.com'
__version__ = '1.3'
__url__ = 'http://deluge-torrent.org'
__license__ = 'GPLv3'
__description__ = 'Plugin to execute a command upon an event'
__long_description__ = __description__
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
