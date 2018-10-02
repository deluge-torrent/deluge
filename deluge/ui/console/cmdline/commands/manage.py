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

from twisted.internet import defer

import deluge.component as component
from deluge.ui.client import client

from . import BaseCommand

log = logging.getLogger(__name__)

torrent_options = {
    'max_download_speed': float,
    'max_upload_speed': float,
    'max_connections': int,
    'max_upload_slots': int,
    'private': bool,
    'prioritize_first_last': bool,
    'is_auto_managed': bool,
    'stop_at_ratio': bool,
    'stop_ratio': float,
    'remove_at_ratio': bool,
    'move_completed': bool,
    'move_completed_path': str,
}


class Command(BaseCommand):
    """Show and manage per-torrent options"""

    usage = _('Usage: manage <torrent-id> [--set <key> <value>] [<key> [<key>...] ]')

    def add_arguments(self, parser):
        parser.add_argument(
            'torrent',
            metavar='<torrent>',
            help=_('an expression matched against torrent ids and torrent names'),
        )
        set_group = parser.add_argument_group('setting a value')
        set_group.add_argument(
            '-s',
            '--set',
            action='store',
            metavar='<key>',
            help=_('set value for this key'),
        )
        set_group.add_argument(
            'values', metavar='<value>', nargs='+', help=_('Value to set')
        )
        get_group = parser.add_argument_group('getting values')
        get_group.add_argument(
            'keys',
            metavar='<keys>',
            nargs='*',
            help=_('one or more keys separated by space'),
        )

    def handle(self, options):
        self.console = component.get('ConsoleUI')
        if options.set:
            return self._set_option(options)
        else:
            return self._get_option(options)

    def _get_option(self, options):
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

        torrent_ids = self.console.match_torrent(options.torrent)

        request_options = []
        for opt in options.values:
            if opt not in torrent_options:
                self.console.write('{!error!}Unknown torrent option: %s' % opt)
                return
            request_options.append(opt)
        if not request_options:
            request_options = list(torrent_options)
        request_options.append('name')

        d = client.core.get_torrents_status({'id': torrent_ids}, request_options)
        d.addCallbacks(on_torrents_status, on_torrents_status_fail)
        return d

    def _set_option(self, options):
        deferred = defer.Deferred()
        key = options.set
        val = ' '.join(options.values)
        torrent_ids = self.console.match_torrent(options.torrent)

        if key not in torrent_options:
            self.console.write('{!error!}Invalid key: %s' % key)
            return

        val = torrent_options[key](val)

        def on_set_config(result):
            self.console.write('{!success!}Torrent option successfully updated.')
            deferred.callback(True)

        self.console.write(
            'Setting %s to %s for torrents %s..' % (key, val, torrent_ids)
        )
        client.core.set_torrent_options(torrent_ids, {key: val}).addCallback(
            on_set_config
        )
        return deferred

    def complete(self, line):
        # We use the ConsoleUI torrent tab complete method
        return component.get('ConsoleUI').tab_complete_torrent(line)
