# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 John Garland <johnnybg+deluge@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase

log = logging.getLogger(__name__)

DEFAULT_PREFS = {}


class Core(CorePluginBase):
    def enable(self):
        self.core = component.get('Core')

    def disable(self):
        pass

    def update(self):
        pass

    @export
    def get_status(self):
        return self.core.session.is_paused()

    @export
    def toggle(self):
        if self.core.session.is_paused():
            self.core.resume_session()
            paused = False
        else:
            self.core.pause_session()
            paused = True
        return paused
