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

from twisted.internet import defer

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand

torrent_options = {
    "max_download_speed": float,
    "max_upload_speed": float,
    "max_connections": int,
    "max_upload_slots": int,
    "private": bool,
    "prioritize_first_last": bool,
    "is_auto_managed": bool,
    "stop_at_ratio": bool,
    "stop_ratio": float,
    "remove_at_ratio": bool,
    "move_on_completed": bool,
    "move_on_completed_path": str
}


class Command(BaseCommand):
    """Show and manage per-torrent options"""

    option_list = BaseCommand.option_list + (
        make_option("-s", "--set", action="store", nargs=2, dest="set", help="set value for key"),
    )
    usage = "Usage: manage <torrent-id> [<key1> [<key2> ...]]\n"\
            "       manage <torrent-id> --set <key> <value>"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")
        if options['set']:
            return self._set_option(*args, **options)
        else:
            return self._get_option(*args, **options)

    def _get_option(self, *args, **options):

        def on_torrents_status(status):
            for torrentid, data in status.items():
                self.console.write('')
                if 'name' in data:
                    self.console.write('{!info!}Name: {!input!}%s' % data.get('name'))
                self.console.write('{!info!}ID: {!input!}%s' % torrentid)
                for k, v in data.items():
                    if k != 'name':
                        self.console.write('{!info!}%s: {!input!}%s' % (k, v))

        def on_torrents_status_fail(reason):
            self.console.write('{!error!}Failed to get torrent data.')

        torrent_ids = []
        torrent_ids.extend(self.console.match_torrent(args[0]))

        request_options = []
        for opt in args[1:]:
            if opt not in torrent_options:
                self.console.write('{!error!}Unknown torrent option: %s' % opt)
                return
            request_options.append(opt)
        if not request_options:
            request_options = [opt for opt in torrent_options.keys()]
        request_options.append('name')

        d = client.core.get_torrents_status({"id": torrent_ids}, request_options)
        d.addCallback(on_torrents_status)
        d.addErrback(on_torrents_status_fail)
        return d

    def _set_option(self, *args, **options):
        deferred = defer.Deferred()
        torrent_ids = []
        torrent_ids.extend(self.console.match_torrent(args[0]))
        key = options["set"][0]
        val = options["set"][1] + " " .join(args[1:])

        if key not in torrent_options:
            self.console.write("{!error!}The key '%s' is invalid!" % key)
            return

        val = torrent_options[key](val)

        def on_set_config(result):
            self.console.write("{!success!}Torrent option successfully updated.")
            deferred.callback(True)

        self.console.write("Setting %s to %s for torrents %s.." % (key, val, torrent_ids))

        for tid in torrent_ids:
            if key == "move_on_completed_path":
                client.core.set_torrent_move_completed_path(tid, val).addCallback(on_set_config)
            elif key == "move_on_completed":
                client.core.set_torrent_move_completed(tid, val).addCallback(on_set_config)
            elif key == "is_auto_managed":
                client.core.set_torrent_auto_managed(tid, val).addCallback(on_set_config)
            elif key == "remove_at_ratio":
                client.core.set_torrent_remove_at_ratio(tid, val).addCallback(on_set_config)
            elif key == "prioritize_first_last":
                client.core.set_torrent_prioritize_first_last(tid, val).addCallback(on_set_config)
            else:
                client.core.set_torrent_options(torrent_ids, {key: val}).addCallback(on_set_config)
                break
        return deferred

    def complete(self, line):
        # We use the ConsoleUI torrent tab complete method
        return component.get("ConsoleUI").tab_complete_torrent(line)
