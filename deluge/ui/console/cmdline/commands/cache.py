# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.common import DISK_CACHE_KEYS

from . import BaseCommand


class Command(BaseCommand):
    """Show information about the disk cache"""

    def handle(self, options):
        self.console = component.get('ConsoleUI')

        def on_cache_status(status):
            for key, value in sorted(status.items()):
                self.console.write('{!info!}%s: {!input!}%s' % (key, value))

        return client.core.get_session_status(DISK_CACHE_KEYS).addCallback(
            on_cache_status
        )
