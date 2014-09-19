# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand


class Command(BaseCommand):
    """Show information about the disk cache"""
    usage = "Usage: cache"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")

        def on_cache_status(status):
            for key, value in status.items():
                self.console.write("{!info!}%s: {!input!}%s" % (key, value))

        d = client.core.get_cache_status()
        d.addCallback(on_cache_status)
        return d
