# -*- coding: utf-8 -*-
#
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

import logging
import os

import pkg_resources

from deluge.plugins.pluginbase import WebPluginBase

log = logging.getLogger(__name__)


def get_resource(filename):
    return pkg_resources.resource_filename("deluge.plugins.label",
                                           os.path.join("data", filename))


class WebUI(WebPluginBase):

    scripts = [get_resource("label.js")]
    debug_scripts = scripts
