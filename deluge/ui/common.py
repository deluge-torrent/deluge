# -*- coding: utf-8 -*-
#
# Copyright (C) Damien Churchill 2008-2009 <damoxc@gmail.com>
# Copyright (C) Andrew Resch 2009 <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""
The ui common module contains methods and classes that are deemed useful for all the interfaces.
"""
from __future__ import unicode_literals

import logging
import os
from hashlib import sha1 as sha

from deluge import bencode
from deluge.common import decode_bytes

log = logging.getLogger(__name__)


# Dummy translation dicts so the text is available for Translators.
#
# All entries in deluge.common.TORRENT_STATE should be added here.
#
# No need to import these, just simply use the `_()` function around a status variable.
def _(message):
    return message


STATE_TRANSLATION = {
    'All': _('All'),
    'Active': _('Active'),
    'Allocating': _('Allocating'),
    'Checking': _('Checking'),
    'Downloading': _('Downloading'),
    'Seeding': _('Seeding'),
    'Paused': _('Paused'),
    'Queued': _('Queued'),
    'Error': _('Error'),
}

TORRENT_DATA_FIELD = {
    'queue': {'name': '#', 'status': ['queue']},
    'name': {'name': _('Name'), 'status': ['state', 'name']},
    'progress_state': {'name': _('Progress'), 'status': ['progress', 'state']},
    'state': {'name': _('State'), 'status': ['state']},
    'progress': {'name': _('Progress'), 'status': ['progress']},
    'size': {'name': _('Size'), 'status': ['total_wanted']},
    'downloaded': {'name': _('Downloaded'), 'status': ['all_time_download']},
    'uploaded': {'name': _('Uploaded'), 'status': ['total_uploaded']},
    'remaining': {'name': _('Remaining'), 'status': ['total_remaining']},
    'ratio': {'name': _('Ratio'), 'status': ['ratio']},
    'download_speed': {'name': _('Down Speed'), 'status': ['download_payload_rate']},
    'upload_speed': {'name': _('Up Speed'), 'status': ['upload_payload_rate']},
    'max_download_speed': {'name': _('Down Limit'), 'status': ['max_download_speed']},
    'max_upload_speed': {'name': _('Up Limit'), 'status': ['max_upload_speed']},
    'max_connections': {'name': _('Max Connections'), 'status': ['max_connections']},
    'max_upload_slots': {'name': _('Max Upload Slots'), 'status': ['max_upload_slots']},
    'peers': {'name': _('Peers'), 'status': ['num_peers', 'total_peers']},
    'seeds': {'name': _('Seeds'), 'status': ['num_seeds', 'total_seeds']},
    'avail': {'name': _('Avail'), 'status': ['distributed_copies']},
    'seeds_peers_ratio': {'name': _('Seeds:Peers'), 'status': ['seeds_peers_ratio']},
    'time_added': {'name': _('Added'), 'status': ['time_added']},
    'tracker': {'name': _('Tracker'), 'status': ['tracker_host']},
    'download_location': {
        'name': _('Download Folder'),
        'status': ['download_location'],
    },
    'seeding_time': {'name': _('Seeding Time'), 'status': ['seeding_time']},
    'active_time': {'name': _('Active Time'), 'status': ['active_time']},
    'time_since_transfer': {
        'name': _('Last Activity'),
        'status': ['time_since_transfer'],
    },
    'finished_time': {'name': _('Finished Time'), 'status': ['finished_time']},
    'last_seen_complete': {
        'name': _('Complete Seen'),
        'status': ['last_seen_complete'],
    },
    'completed_time': {'name': _('Completed'), 'status': ['completed_time']},
    'eta': {'name': _('ETA'), 'status': ['eta']},
    'shared': {'name': _('Shared'), 'status': ['shared']},
    'prioritize_first_last': {
        'name': _('Prioritize First/Last'),
        'status': ['prioritize_first_last'],
    },
    'sequential_download': {
        'name': _('Sequential Download'),
        'status': ['sequential_download'],
    },
    'is_auto_managed': {'name': _('Auto Managed'), 'status': ['is_auto_managed']},
    'auto_managed': {'name': _('Auto Managed'), 'status': ['auto_managed']},
    'stop_at_ratio': {'name': _('Stop At Ratio'), 'status': ['stop_at_ratio']},
    'stop_ratio': {'name': _('Stop Ratio'), 'status': ['stop_ratio']},
    'remove_at_ratio': {'name': _('Remove At Ratio'), 'status': ['remove_at_ratio']},
    'move_completed': {'name': _('Move On Completed'), 'status': ['move_completed']},
    'move_completed_path': {
        'name': _('Move Completed Path'),
        'status': ['move_completed_path'],
    },
    'move_on_completed': {
        'name': _('Move On Completed'),
        'status': ['move_on_completed'],
    },
    'move_on_completed_path': {
        'name': _('Move On Completed Path'),
        'status': ['move_on_completed_path'],
    },
    'owner': {'name': _('Owner'), 'status': ['owner']},
    'pieces': {'name': _('Pieces'), 'status': ['num_pieces', 'piece_length']},
    'seed_rank': {'name': _('Seed Rank'), 'status': ['seed_rank']},
    'super_seeding': {'name': _('Super Seeding'), 'status': ['super_seeding']},
}

TRACKER_STATUS_TRANSLATION = [
    _('Error'),
    _('Warning'),
    _('Announce OK'),
    _('Announce Sent'),
]

PREFS_CATOG_TRANS = {
    'interface': _('Interface'),
    'downloads': _('Downloads'),
    'bandwidth': _('Bandwidth'),
    'queue': _('Queue'),
    'network': _('Network'),
    'proxy': _('Proxy'),
    'cache': _('Cache'),
    'other': _('Other'),
    'daemon': _('Daemon'),
    'plugins': _('Plugins'),
}

FILE_PRIORITY = {
    0: 'Skip',
    1: 'Low',
    2: 'Low',
    3: 'Low',
    4: 'Normal',
    5: 'High',
    6: 'High',
    7: 'High',
    _('Skip'): 0,
    _('Low'): 1,
    _('Normal'): 4,
    _('High'): 7,
}

del _

# The keys from session statistics for cache status.
DISK_CACHE_KEYS = [
    'disk.num_blocks_read',
    'disk.num_blocks_written',
    'disk.num_read_ops',
    'disk.num_write_ops',
    'disk.num_blocks_cache_hits',
    'read_hit_ratio',
    'write_hit_ratio',
    'disk.disk_blocks_in_use',
    'disk.read_cache_blocks',
]


class TorrentInfo(object):
    """Collects information about a torrent file.

    Args:
        filename (str, optional): The path to the .torrent file.
        filetree (int, optional): The version of filetree to create (defaults to 1).
        torrent_file (dict, optional): A bdecoded .torrent file contents.

    """

    def __init__(self, filename='', filetree=1, torrent_file=None):
        self._filedata = None
        if torrent_file:
            self._metainfo = torrent_file
        elif filename:
            log.debug('Attempting to open %s.', filename)
            try:
                with open(filename, 'rb') as _file:
                    self._filedata = _file.read()
            except IOError as ex:
                log.warning('Unable to open %s: %s', filename, ex)
                return

            try:
                self._metainfo = bencode.bdecode(self._filedata)
            except bencode.BTFailure as ex:
                log.warning('Failed to decode %s: %s', filename, ex)
                return
        else:
            log.warning('Requires valid arguments.')
            return

        # info_dict with keys decoded to unicode.
        info_dict = {k.decode(): v for k, v in self._metainfo[b'info'].items()}
        self._info_hash = sha(bencode.bencode(info_dict)).hexdigest()

        # Get encoding from torrent file if available
        encoding = info_dict.get(
            'encoding', info_dict.get('codepage', b'UTF-8')
        ).decode()

        # Decode 'name' with encoding unless 'name.utf-8' found.
        if 'name.utf-8' in info_dict:
            self._name = decode_bytes(info_dict['name.utf-8'])
        else:
            self._name = decode_bytes(info_dict['name'], encoding)

        # Get list of files from torrent info
        self._files = []
        if 'files' in info_dict:
            paths = {}
            dirs = {}
            prefix = self._name if len(info_dict['files']) > 1 else ''

            for index, f in enumerate(info_dict['files']):
                f = {k.decode(): v for k, v in f.items()}

                if 'path.utf-8' in f:
                    path = decode_bytes(os.path.join(*f['path.utf-8']))
                else:
                    path = decode_bytes(os.path.join(*f['path']), encoding)

                if prefix:
                    path = os.path.join(prefix, path)

                # Ensure agnostic path separator
                path = path.replace('\\', '/')

                self._files.append(
                    {'path': path, 'size': f['length'], 'download': True}
                )
                paths[path] = {'path': path, 'index': index, 'length': f['length']}

                dirname = os.path.dirname(path)
                while dirname:
                    dirinfo = dirs.setdefault(dirname, {})
                    dirinfo['length'] = dirinfo.get('length', 0) + f['length']
                    dirname = os.path.dirname(dirname)

            if filetree == 2:

                def walk(path, item):
                    if item['type'] == 'dir':
                        item.update(dirs[path])
                    else:
                        item.update(paths[path])
                    item['download'] = True

                file_tree = FileTree2(list(paths))
                file_tree.walk(walk)
            else:

                def walk(path, item):
                    if isinstance(item, dict):
                        return item
                    return [paths[path]['index'], paths[path]['length'], True]

                file_tree = FileTree(paths)
                file_tree.walk(walk)
            self._files_tree = file_tree.get_tree()
        else:
            self._files.append(
                {'path': self._name, 'size': info_dict['length'], 'download': True}
            )
            if filetree == 2:
                self._files_tree = {
                    'contents': {
                        self._name: {
                            'type': 'file',
                            'index': 0,
                            'length': info_dict['length'],
                            'download': True,
                        }
                    }
                }
            else:
                self._files_tree = {self._name: (0, info_dict['length'], True)}

    @classmethod
    def from_metadata(cls, metadata, trackers=None):
        """Create a TorrentInfo from metadata and trackers

        Args:
            metadata (dict): A bdecoded info section of torrent file.
            trackers (list of lists, optional): The trackers to include.

        """
        if not isinstance(metadata, dict):
            return

        metainfo = {b'info': metadata}
        if trackers:
            metainfo[b'announce'] = trackers[0][0].encode('utf-8')
            trackers_utf8 = [[t.encode('utf-8') for t in tier] for tier in trackers]
            metainfo[b'announce-list'] = trackers_utf8
        return cls(torrent_file=metainfo)

    def as_dict(self, *keys):
        """The torrent info as a dictionary, filtered by keys.

        Args:
            keys (str): A space-separated string of keys.

        Returns:
            dict: The torrent info dict with specified keys.
        """
        return {key: getattr(self, key) for key in keys}

    @property
    def name(self):
        """The name of the torrent.

        Returns:
            str: The torrent name.

        """
        return self._name

    @property
    def info_hash(self):
        """The calculated torrent info_hash.

        Returns:
            str: The torrent info_hash.
        """
        return self._info_hash

    @property
    def files(self):
        """The files that the torrent contains.

        Returns:
            list: The list of torrent files.

        """
        return self._files

    @property
    def files_tree(self):
        """A tree of the files the torrent contains.

        ::

            {
                "some_directory": {
                    "some_file": (index, size, download)
                }
            }

        Returns:
            dict: The tree of files.

        """
        return self._files_tree

    @property
    def metainfo(self):
        """Returns the torrent metainfo dictionary.

        This is the bdecoded torrent file contents.

        Returns:
            dict: The metainfo dictionary.

        """
        return self._metainfo

    @property
    def filedata(self):
        """The contents of the .torrent file.

        Returns:
            bytes: The bencoded metainfo.

        """
        if not self._filedata:
            self._filedata = bencode.bencode(self._metainfo)
        return self._filedata


class FileTree2(object):
    """
    Converts a list of paths in to a file tree.

    :param paths: The paths to be converted
    :type paths: list
    """

    def __init__(self, paths):
        self.tree = {'contents': {}, 'type': 'dir'}

        def get_parent(path):
            parent = self.tree
            while '/' in path:
                directory, path = path.split('/', 1)
                child = parent['contents'].get(directory)
                if child is None:
                    parent['contents'][directory] = {'type': 'dir', 'contents': {}}
                parent = parent['contents'][directory]
            return parent, path

        for path in paths:
            if path[-1] == '/':
                path = path[:-1]
                parent, path = get_parent(path)
                parent['contents'][path] = {'type': 'dir', 'contents': {}}
            else:
                parent, path = get_parent(path)
                parent['contents'][path] = {'type': 'file'}

    def get_tree(self):
        """
        Return the tree.

        :returns: the file tree.
        :rtype: dictionary
        """
        return self.tree

    def walk(self, callback):
        """
        Walk through the file tree calling the callback function on each item
        contained.

        :param callback: The function to be used as a callback, it should have
            the signature func(item, path) where item is a `tuple` for a file
            and `dict` for a directory.
        :type callback: function
        """

        def walk(directory, parent_path):
            for path in list(directory['contents']):
                full_path = os.path.join(parent_path, path).replace('\\', '/')
                if directory['contents'][path]['type'] == 'dir':
                    directory['contents'][path] = (
                        callback(full_path, directory['contents'][path])
                        or directory['contents'][path]
                    )
                    walk(directory['contents'][path], full_path)
                else:
                    directory['contents'][path] = (
                        callback(full_path, directory['contents'][path])
                        or directory['contents'][path]
                    )

        walk(self.tree, '')

    def __str__(self):
        lines = []

        def write(path, item):
            depth = path.count('/')
            path = os.path.basename(path)
            path = path + '/' if item['type'] == 'dir' else path
            lines.append('  ' * depth + path)

        self.walk(write)
        return '\n'.join(lines)


class FileTree(object):
    """
    Convert a list of paths in a file tree.

    :param paths: The paths to be converted.
    :type paths: list
    """

    def __init__(self, paths):
        self.tree = {}

        def get_parent(path):
            parent = self.tree
            while '/' in path:
                directory, path = path.split('/', 1)
                child = parent.get(directory)
                if child is None:
                    parent[directory] = {}
                parent = parent[directory]
            return parent, path

        for path in paths:
            if path[-1] == '/':
                path = path[:-1]
                parent, path = get_parent(path)
                parent[path] = {}
            else:
                parent, path = get_parent(path)
                parent[path] = []

    def get_tree(self):
        """
        Return the tree, after first converting all file lists to a tuple.

        :returns: the file tree.
        :rtype: dictionary
        """

        def to_tuple(path, item):
            if isinstance(item, dict):
                return item
            return tuple(item)

        self.walk(to_tuple)
        return self.tree

    def walk(self, callback):
        """
        Walk through the file tree calling the callback function on each item
        contained.

        :param callback: The function to be used as a callback, it should have
            the signature func(item, path) where item is a `tuple` for a file
            and `dict` for a directory.
        :type callback: function
        """

        def walk(directory, parent_path):
            for path in list(directory):
                full_path = os.path.join(parent_path, path).replace('\\', '/')
                if isinstance(directory[path], dict):
                    directory[path] = (
                        callback(full_path, directory[path]) or directory[path]
                    )
                    walk(directory[path], full_path)
                else:
                    directory[path] = (
                        callback(full_path, directory[path]) or directory[path]
                    )

        walk(self.tree, '')

    def __str__(self):
        lines = []

        def write(path, item):
            depth = path.count('/')
            path = os.path.basename(path)
            path = isinstance(item, dict) and path + '/' or path
            lines.append('  ' * depth + path)

        self.walk(write)
        return '\n'.join(lines)
