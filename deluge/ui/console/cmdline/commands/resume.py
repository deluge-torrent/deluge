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

from . import BaseCommand


class Command(BaseCommand):
    """Resume torrents"""

    usage = _('Usage: resume [ * | <torrent-id> [<torrent-id> ...] ]')

    def add_arguments(self, parser):
        parser.add_argument(
            'torrent_ids',
            metavar='<torrent-id>',
            nargs='+',
            help=_('One or more torrent ids. Use "*" to resume all torrents'),
        )

    def handle(self, options):
        self.console = component.get('ConsoleUI')

        if options.torrent_ids[0] == '*':
            client.core.resume_session()
            return

        torrent_ids = []
        for t_id in options.torrent_ids:
            torrent_ids.extend(self.console.match_torrent(t_id))

        if torrent_ids:
            return client.core.resume_torrent(torrent_ids)

    def complete(self, line):
        # We use the ConsoleUI torrent tab complete method
        return component.get('ConsoleUI').tab_complete_torrent(line)
