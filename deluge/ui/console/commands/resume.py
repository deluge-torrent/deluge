# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
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
    """Resume a torrent"""
    usage = "Usage: resume [ * | <torrent-id> [<torrent-id> ...] ]"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")

        if len(args) == 0:
            self.console.write(self.usage)
            return
        if len(args) > 0 and args[0] == "*":
            client.core.resume_session()
            return

        torrent_ids = []
        for arg in args:
            torrent_ids.extend(self.console.match_torrent(arg))

        if torrent_ids:
            return client.core.resume_torrent(torrent_ids)

    def complete(self, line):
        # We use the ConsoleUI torrent tab complete method
        return component.get("ConsoleUI").tab_complete_torrent(line)
