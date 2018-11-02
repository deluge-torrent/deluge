# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import division, unicode_literals

from os.path import sep as dirsep

import deluge.component as component
import deluge.ui.console.utils.colors as colors
from deluge.common import TORRENT_STATE, fsize, fspeed
from deluge.ui.client import client
from deluge.ui.common import FILE_PRIORITY
from deluge.ui.console.utils.format_utils import (
    f_progressbar,
    f_seedrank_dash,
    format_date_never,
    format_progress,
    format_time,
    ftotal_sized,
    pad_string,
    remove_formatting,
    shorten_hash,
    strwidth,
    trim_string,
)

from . import BaseCommand

STATUS_KEYS = [
    'state',
    'download_location',
    'tracker_host',
    'tracker_status',
    'next_announce',
    'name',
    'total_size',
    'progress',
    'num_seeds',
    'total_seeds',
    'num_peers',
    'total_peers',
    'eta',
    'download_payload_rate',
    'upload_payload_rate',
    'ratio',
    'distributed_copies',
    'num_pieces',
    'piece_length',
    'total_done',
    'files',
    'file_priorities',
    'file_progress',
    'peers',
    'is_seed',
    'is_finished',
    'active_time',
    'seeding_time',
    'time_since_transfer',
    'last_seen_complete',
    'seed_rank',
    'all_time_download',
    'total_uploaded',
    'total_payload_download',
    'total_payload_upload',
    'time_added',
]

# Add filter specific state to torrent states
STATES = ['Active'] + TORRENT_STATE


class Command(BaseCommand):
    """Show information about the torrents"""

    sort_help = 'sort items.  Possible keys: ' + ', '.join(STATUS_KEYS)

    epilog = """
  You can give the first few characters of a torrent-id to identify the torrent.

  Tab Completion in interactive mode (info *pattern*<tab>):\n
      | First press of <tab> will output up to 15 matches;
      | hitting <tab> a second time, will print 15 more matches;
      | and a third press will print all remaining matches.
      | (To modify behaviour of third <tab>, set `third_tab_lists_all` to False)
"""

    def add_arguments(self, parser):
        parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            default=False,
            dest='verbose',
            help=_('Show more information per torrent.'),
        )
        parser.add_argument(
            '-d',
            '--detailed',
            action='store_true',
            default=False,
            dest='detailed',
            help=_('Show more detailed information including files and peers.'),
        )
        parser.add_argument(
            '-s',
            '--state',
            action='store',
            dest='state',
            help=_('Show torrents with state STATE: %s.' % (', '.join(STATES))),
        )
        parser.add_argument(
            '--sort',
            action='store',
            type=str,
            default='',
            dest='sort',
            help=self.sort_help,
        )
        parser.add_argument(
            '--sort-reverse',
            action='store',
            type=str,
            default='',
            dest='sort_rev',
            help=_('Same as --sort but items are in reverse order.'),
        )
        parser.add_argument(
            'torrent_ids',
            metavar='<torrent-id>',
            nargs='*',
            help=_('One or more torrent ids. If none is given, list all'),
        )

    def add_subparser(self, subparsers):
        parser = subparsers.add_parser(
            self.name,
            prog=self.name,
            help=self.__doc__,
            description=self.__doc__,
            epilog=self.epilog,
        )
        self.add_arguments(parser)

    def handle(self, options):
        self.console = component.get('ConsoleUI')
        # Compile a list of torrent_ids to request the status of
        torrent_ids = []

        if options.torrent_ids:
            for t_id in options.torrent_ids:
                torrent_ids.extend(self.console.match_torrent(t_id))
        else:
            torrent_ids.extend(self.console.match_torrent(''))

        def on_torrents_status(status):
            # Print out the information for each torrent
            sort_key = options.sort
            sort_reverse = False
            if not sort_key:
                sort_key = options.sort_rev
                sort_reverse = True
            if not sort_key:
                sort_key = 'name'
                sort_reverse = False
            if sort_key not in STATUS_KEYS:
                self.console.write('')
                self.console.write(
                    '{!error!}Unknown sort key: ' + sort_key + ', will sort on name'
                )
                sort_key = 'name'
                sort_reverse = False
            for key, value in sorted(
                list(status.items()),
                key=lambda x: x[1].get(sort_key),
                reverse=sort_reverse,
            ):
                self.show_info(key, status[key], options.verbose, options.detailed)

        def on_torrents_status_fail(reason):
            self.console.write('{!error!}Error getting torrent info: %s' % reason)

        status_dict = {'id': torrent_ids}

        if options.state:
            options.state = options.state.capitalize()
            if options.state in STATES:
                status_dict.state = options.state
            else:
                self.console.write('Invalid state: %s' % options.state)
                self.console.write('Possible values are: %s.' % (', '.join(STATES)))
                return

        d = client.core.get_torrents_status(status_dict, STATUS_KEYS)
        d.addCallback(on_torrents_status)
        d.addErrback(on_torrents_status_fail)
        return d

    def show_file_info(self, torrent_id, status):
        spaces_per_level = 2

        if hasattr(self.console, 'screen'):
            cols = self.console.screen.cols
        else:
            cols = 80

        prevpath = []
        for index, torrent_file in enumerate(status['files']):
            filename = torrent_file['path'].split(dirsep)[-1]
            filepath = torrent_file['path'].split(dirsep)[:-1]

            for depth, subdir in enumerate(filepath):
                indent = ' ' * depth * spaces_per_level
                if depth >= len(prevpath):
                    self.console.write('%s{!cyan!}%s' % (indent, subdir))
                elif subdir != prevpath[depth]:
                    self.console.write('%s{!cyan!}%s' % (indent, subdir))

            depth = len(filepath)

            indent = ' ' * depth * spaces_per_level

            col_filename = indent + filename
            col_size = ' ({!cyan!}%s{!input!})' % fsize(torrent_file['size'])
            col_progress = ' {!input!}%.2f%%' % (status['file_progress'][index] * 100)

            col_priority = ' {!info!}Priority: '

            file_priority = FILE_PRIORITY[status['file_priorities'][index]]

            if status['file_progress'][index] != 1.0:
                if file_priority == 'Skip':
                    col_priority += '{!error!}'
                else:
                    col_priority += '{!success!}'
            else:
                col_priority += '{!input!}'
            col_priority += file_priority

            def tlen(string):
                return strwidth(remove_formatting(string))

            col_all_info = col_size + col_progress + col_priority
            # Check how much space we've got left after writing all the info
            space_left = cols - tlen(col_all_info)
            # And how much we will potentially have with the longest possible column
            maxlen_space_left = cols - tlen(' (1000.0 MiB) 100.00% Priority: Normal')
            if maxlen_space_left > tlen(col_filename) + 1:
                # If there is enough space, pad it all nicely
                col_all_info = ''
                col_all_info += ' ('
                spaces_to_add = tlen(' (1000.0 MiB)') - tlen(col_size)
                col_all_info += ' ' * spaces_to_add
                col_all_info += col_size[2:]
                spaces_to_add = tlen(' 100.00%') - tlen(col_progress)
                col_all_info += ' ' * spaces_to_add
                col_all_info += col_progress
                spaces_to_add = tlen(' Priority: Normal') - tlen(col_priority)
                col_all_info += col_priority
                col_all_info += ' ' * spaces_to_add
                # And remember to put it to the left!
                col_filename = pad_string(
                    col_filename, maxlen_space_left - 2, side='right'
                )
            elif space_left > tlen(col_filename) + 1:
                # If there is enough space, put the info to the right
                col_filename = pad_string(col_filename, space_left - 2, side='right')
            else:
                # And if there is not, shorten the name
                col_filename = trim_string(col_filename, space_left, True)
            self.console.write(col_filename + col_all_info)

            prevpath = filepath

    def show_peer_info(self, torrent_id, status):
        if len(status['peers']) == 0:
            self.console.write('    None')
        else:
            s = ''
            for peer in status['peers']:
                if peer['seed']:
                    s += '%sSeed\t{!input!}' % colors.state_color['Seeding']
                else:
                    s += '%sPeer\t{!input!}' % colors.state_color['Downloading']

                s += peer['country'] + '\t'

                if peer['ip'].count(':') == 1:
                    # IPv4
                    s += peer['ip']
                else:
                    # IPv6
                    s += '[%s]:%s' % (
                        ':'.join(peer['ip'].split(':')[:-1]),
                        peer['ip'].split(':')[-1],
                    )

                c = peer['client']
                s += '\t' + c

                if len(c) < 16:
                    s += '\t\t'
                else:
                    s += '\t'
                s += '%s%s\t%s%s' % (
                    colors.state_color['Seeding'],
                    fspeed(peer['up_speed']),
                    colors.state_color['Downloading'],
                    fspeed(peer['down_speed']),
                )
                s += '\n'

            self.console.write(s[:-1])

    def show_info(self, torrent_id, status, verbose=False, detailed=False):
        """
        Writes out the torrents information to the screen.

        Format depends on switches given.
        """
        self.console.set_batch_write(True)

        if hasattr(self.console, 'screen'):
            cols = self.console.screen.cols
        else:
            cols = 80

        sep = ' '

        if verbose or detailed:
            self.console.write('{!info!}Name: {!input!}%s' % (status['name']))
            self.console.write('{!info!}ID: {!input!}%s' % (torrent_id))
            s = '{!info!}State: %s%s' % (
                colors.state_color[status['state']],
                status['state'],
            )
            # Only show speed if active
            if status['state'] in ('Seeding', 'Downloading'):
                if status['state'] != 'Seeding':
                    s += sep
                    s += '{!info!}Down Speed: {!input!}%s' % fspeed(
                        status['download_payload_rate'], shortform=True
                    )
                s += sep
                s += '{!info!}Up Speed: {!input!}%s' % fspeed(
                    status['upload_payload_rate'], shortform=True
                )
            self.console.write(s)

            if status['state'] in ('Seeding', 'Downloading', 'Queued'):
                s = '{!info!}Seeds: {!input!}%s (%s)' % (
                    status['num_seeds'],
                    status['total_seeds'],
                )
                s += sep
                s += '{!info!}Peers: {!input!}%s (%s)' % (
                    status['num_peers'],
                    status['total_peers'],
                )
                s += sep
                s += (
                    '{!info!}Availability: {!input!}%.2f' % status['distributed_copies']
                )
                s += sep
                s += '{!info!}Seed Rank: {!input!}%s' % f_seedrank_dash(
                    status['seed_rank'], status['seeding_time']
                )
                self.console.write(s)

            total_done = fsize(status['total_done'], shortform=True)
            total_size = fsize(status['total_size'], shortform=True)
            if total_done == total_size:
                s = '{!info!}Size: {!input!}%s' % (total_size)
            else:
                s = '{!info!}Size: {!input!}%s/%s' % (total_done, total_size)
            s += sep
            s += '{!info!}Downloaded: {!input!}%s' % fsize(
                status['all_time_download'], shortform=True
            )
            s += sep
            s += '{!info!}Uploaded: {!input!}%s' % fsize(
                status['total_uploaded'], shortform=True
            )
            s += sep
            s += '{!info!}Share Ratio: {!input!}%.2f' % status['ratio']
            self.console.write(s)

            s = '{!info!}ETA: {!input!}%s' % format_time(status['eta'])
            s += sep
            s += '{!info!}Seeding: {!input!}%s' % format_time(status['seeding_time'])
            s += sep
            s += '{!info!}Active: {!input!}%s' % format_time(status['active_time'])
            self.console.write(s)

            s = '{!info!}Last Transfer: {!input!}%s' % format_time(
                status['time_since_transfer']
            )
            s += sep
            s += '{!info!}Complete Seen: {!input!}%s' % format_date_never(
                status['last_seen_complete']
            )
            self.console.write(s)

            s = '{!info!}Tracker: {!input!}%s' % status['tracker_host']
            self.console.write(s)

            self.console.write(
                '{!info!}Tracker status: {!input!}%s' % status['tracker_status']
            )

            if not status['is_finished']:
                pbar = f_progressbar(
                    status['progress'], cols - (13 + len('%.2f%%' % status['progress']))
                )
                s = '{!info!}Progress: {!input!}%.2f%% %s' % (status['progress'], pbar)
                self.console.write(s)

            s = '{!info!}Download Folder: {!input!}%s' % status['download_location']
            self.console.write(s + '\n')

            if detailed:
                self.console.write('{!info!}Files in torrent')
                self.show_file_info(torrent_id, status)
                self.console.write('{!info!}Connected peers')
                self.show_peer_info(torrent_id, status)
        else:
            up_color = colors.state_color['Seeding']
            down_color = colors.state_color['Downloading']

            s = '%s%s' % (
                colors.state_color[status['state']],
                '[' + status['state'][0] + ']',
            )

            s += ' {!info!}' + format_progress(status['progress']).rjust(6, ' ')
            s += ' {!input!}%s' % (status['name'])

            # Shorten the ID if it's necessary. Pretty hacky
            # XXX: should make a nice function for it that can partition and shorten stuff
            space_left = cols - strwidth('[S] 99.99% ' + status['name'])

            if self.console.interactive and space_left >= len(sep + torrent_id):
                # Not enough line space so shorten the hash (for interactive mode).
                torrent_id = shorten_hash(torrent_id, space_left)
            s += sep
            s += '{!cyan!}%s' % torrent_id
            self.console.write(s)

            dl_info = '{!info!}DL: {!input!}'
            dl_info += '%s' % ftotal_sized(
                status['all_time_download'], status['total_payload_download']
            )

            if status['download_payload_rate'] > 0:
                dl_info += ' @ %s%s' % (
                    down_color,
                    fspeed(status['download_payload_rate'], shortform=True),
                )

            ul_info = ' {!info!}UL: {!input!}'
            ul_info += '%s' % ftotal_sized(
                status['total_uploaded'], status['total_payload_upload']
            )
            if status['upload_payload_rate'] > 0:
                ul_info += ' @ %s%s' % (
                    up_color,
                    fspeed(status['upload_payload_rate'], shortform=True),
                )

            eta = ' {!info!}ETA: {!magenta!}%s' % format_time(status['eta'])

            self.console.write('    ' + dl_info + ul_info + eta + '\n')

        self.console.set_batch_write(False)

    def complete(self, line):
        # We use the ConsoleUI torrent tab complete method
        return component.get('ConsoleUI').tab_complete_torrent(line)
