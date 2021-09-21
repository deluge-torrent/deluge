# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component
from deluge.ui.client import client

from . import BaseCommand

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Remove a torrent"""

    aliases = ['del']

    def add_arguments(self, parser):
        parser.add_argument(
            '--remove_data',
            action='store_true',
            default=False,
            help=_('Also removes the torrent data'),
        )
        parser.add_argument(
            '-c',
            '--confirm',
            action='store_true',
            default=False,
            help=_('List the matching torrents without removing.'),
        )
        parser.add_argument(
            'torrent_ids',
            metavar='<torrent-id>',
            nargs='+',
            help=_('One or more torrent ids'),
        )

    def handle(self, options):
        self.console = component.get('ConsoleUI')
        torrent_ids = self.console.match_torrents(options.torrent_ids)

        if not options.confirm:
            self.console.write(
                '{!info!}%d %s %s{!info!}'
                % (
                    len(torrent_ids),
                    _n('torrent', 'torrents', len(torrent_ids)),
                    _n('match', 'matches', len(torrent_ids)),
                )
            )
            for t_id in torrent_ids:
                name = self.console.get_torrent_name(t_id)
                self.console.write('* %-50s (%s)' % (name, t_id))
            self.console.write(
                _('Confirm with -c to remove the listed torrents (Count: %d)')
                % len(torrent_ids)
            )
            return

        def on_removed_finished(errors):
            if errors:
                self.console.write(
                    'Error(s) occurred when trying to delete torrent(s).'
                )
                for t_id, e_msg in errors:
                    self.console.write('Error removing torrent %s : %s' % (t_id, e_msg))

        log.info('Removing %d torrents', len(torrent_ids))
        d = client.core.remove_torrents(torrent_ids, options.remove_data)
        d.addCallback(on_removed_finished)

    def complete(self, line):
        # We use the ConsoleUI torrent tab complete method
        return component.get('ConsoleUI').tab_complete_torrent(line)
