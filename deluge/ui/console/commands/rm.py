# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from optparse import make_option

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand


class Command(BaseCommand):
    """Remove a torrent"""
    usage = "Usage: rm <torrent-id>"
    aliases = ["del"]

    option_list = BaseCommand.option_list + (
        make_option("--remove_data", action="store_true", default=False,
                    help="remove the torrent's data"),
    )

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")
        if len(args) == 0:
            self.console.write(self.usage)

        torrent_ids = []
        for arg in args:
            torrent_ids.extend(self.console.match_torrent(arg))

        def on_removed_finished(errors):
            if errors:
                self.console.write("Error(s) occured when trying to delete torrent(s).")
                for t_id, e_msg in errors:
                    self.console.write("Error removing torrent %s : %s" % (t_id, e_msg))

        d = client.core.remove_torrents(torrent_ids, options["remove_data"])
        d.addCallback(on_removed_finished)

    def complete(self, line):
        # We use the ConsoleUI torrent tab complete method
        return component.get("ConsoleUI").tab_complete_torrent(line)
