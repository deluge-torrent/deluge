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

from __future__ import unicode_literals

import logging

from deluge.plugins.pluginbase import WebPluginBase

from .common import get_resource

log = logging.getLogger(__name__)


class WebUI(WebPluginBase):

    scripts = [get_resource('stats.js')]

    # The enable and disable methods are not scrictly required on the WebUI
    # plugins. They are only here if you need to register images/stylesheets
    # with the webserver.
    def enable(self):
        log.debug('Stats Web plugin enabled!')

    def disable(self):
        log.debug('Stats Web plugin disabled!')
