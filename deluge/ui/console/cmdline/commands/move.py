# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os.path

import deluge.component as component
from deluge.ui.client import client

from . import BaseCommand

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Move torrents' storage location"""

    def add_arguments(self, parser):
        parser.add_argument(
            'torrent_ids',
            metavar='<torrent-id>',
            nargs='+',
            help=_('One or more torrent ids'),
        )
        parser.add_argument(
            'path', metavar='<path>', help=_('The path to move the torrents to')
        )

    def handle(self, options):
        self.console = component.get('ConsoleUI')

        if os.path.exists(options.path) and not os.path.isdir(options.path):
            self.console.write(
                '{!error!}Cannot Move Download Folder: %s exists and is not a directory'
                % options.path
            )
            return

        ids = []
        names = []
        for t_id in options.torrent_ids:
            tid = self.console.match_torrent(t_id)
            ids.extend(tid)
            names.append(self.console.get_torrent_name(tid))

        def on_move(res):
            msg = 'Moved "%s" to %s' % (', '.join(names), options.path)
            self.console.write(msg)
            log.info(msg)

        d = client.core.move_storage(ids, options.path)
        d.addCallback(on_move)
        return d

    def complete(self, line):
        line = os.path.abspath(os.path.expanduser(line))
        ret = []
        if os.path.exists(line):
            # This is a correct path, check to see if it's a directory
            if os.path.isdir(line):
                # Directory, so we need to show contents of directory
                # ret.extend(os.listdir(line))
                for f in os.listdir(line):
                    # Skip hidden
                    if f.startswith('.'):
                        continue
                    f = os.path.join(line, f)
                    if os.path.isdir(f):
                        f += '/'
                    ret.append(f)
            else:
                # This is a file, but we could be looking for another file that
                # shares a common prefix.
                for f in os.listdir(os.path.dirname(line)):
                    if f.startswith(os.path.split(line)[1]):
                        ret.append(os.path.join(os.path.dirname(line), f))
        else:
            # This path does not exist, so lets do a listdir on it's parent
            # and find any matches.
            ret = []
            if os.path.isdir(os.path.dirname(line)):
                for f in os.listdir(os.path.dirname(line)):
                    if f.startswith(os.path.split(line)[1]):
                        p = os.path.join(os.path.dirname(line), f)

                        if os.path.isdir(p):
                            p += '/'
                        ret.append(p)
        return ret
