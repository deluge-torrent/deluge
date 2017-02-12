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
import time
from hashlib import sha1 as sha

import deluge.configmanager
from deluge import bencode
from deluge.common import utf8_encoded

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
    'queue':                     {'name': '#', 'status': ['queue']},
    'name':                      {'name': _('Name'), 'status': ['state', 'name']},
    'progress_state':            {'name': _('Progress'), 'status': ['progress', 'state']},
    'state':                     {'name': _('State'), 'status': ['state']},
    'progress':                  {'name': _('Progress'), 'status': ['progress']},
    'size':                      {'name': _('Size'), 'status': ['total_wanted']},
    'downloaded':                {'name': _('Downloaded'), 'status': ['all_time_download']},
    'uploaded':                  {'name': _('Uploaded'), 'status': ['total_uploaded']},
    'remaining':                 {'name': _('Remaining'), 'status': ['total_remaining']},
    'ratio':                     {'name': _('Ratio'), 'status': ['ratio']},
    'download_speed':            {'name': _('Down Speed'), 'status': ['download_payload_rate']},
    'upload_speed':              {'name': _('Up Speed'), 'status': ['upload_payload_rate']},
    'max_download_speed':        {'name': _('Down Limit'), 'status': ['max_download_speed']},
    'max_upload_speed':          {'name': _('Up Limit'), 'status': ['max_upload_speed']},
    'max_connections':           {'name': _('Max Connections'), 'status': ['max_connections']},
    'max_upload_slots':          {'name': _('Max Upload Slots'), 'status': ['max_upload_slots']},
    'peers':                     {'name': _('Peers'), 'status': ['num_peers', 'total_peers']},
    'seeds':                     {'name': _('Seeds'), 'status': ['num_seeds', 'total_seeds']},
    'avail':                     {'name': _('Avail'), 'status': ['distributed_copies']},
    'seeds_peers_ratio':         {'name': _('Seeds:Peers'), 'status': ['seeds_peers_ratio']},
    'time_added':                {'name': _('Added'), 'status': ['time_added']},
    'tracker':                   {'name': _('Tracker'), 'status': ['tracker_host']},
    'download_location':         {'name': _('Download Folder'), 'status': ['download_location']},
    'seeding_time':              {'name': _('Seeding Time'), 'status': ['seeding_time']},
    'active_time':               {'name': _('Active Time'), 'status': ['active_time']},
    'finished_time':             {'name': _('Finished Time'), 'status': ['finished_time']},
    'last_seen_complete':        {'name': _('Complete Seen'), 'status': ['last_seen_complete']},
    'completed_time':            {'name': _('Completed'), 'status': ['completed_time']},
    'eta':                       {'name': _('ETA'), 'status': ['eta']},
    'shared':                    {'name': _('Shared'), 'status': ['shared']},
    'prioritize_first_last':     {'name': _('Prioritize First/Last'), 'status': ['prioritize_first_last']},
    'sequential_download':       {'name': _('Sequential Download'), 'status': ['sequential_download']},
    'is_auto_managed':           {'name': _('Auto Managed'), 'status': ['is_auto_managed']},
    'auto_managed':              {'name': _('Auto Managed'), 'status': ['auto_managed']},
    'stop_at_ratio':             {'name': _('Stop At Ratio'), 'status': ['stop_at_ratio']},
    'stop_ratio':                {'name': _('Stop Ratio'), 'status': ['stop_ratio']},
    'remove_at_ratio':           {'name': _('Remove At Ratio'), 'status': ['remove_at_ratio']},
    'move_completed':            {'name': _('Move On Completed'), 'status': ['move_completed']},
    'move_completed_path':       {'name': _('Move Completed Path'), 'status': ['move_completed_path']},
    'move_on_completed':         {'name': _('Move On Completed'), 'status': ['move_on_completed']},
    'move_on_completed_path':    {'name': _('Move On Completed Path'), 'status': ['move_on_completed_path']},
    'owner':                     {'name': _('Owner'), 'status': ['owner']}
}

TRACKER_STATUS_TRANSLATION = [
    _('Error'),
    _('Warning'),
    _('Announce OK'),
    _('Announce Sent')
]

FILE_PRIORITY = {
    0: 'Ignore',
    1: 'Low',
    2: 'Low',
    3: 'Low',
    4: 'Normal',
    5: 'High',
    6: 'High',
    7: 'High',
    _('Ignore'): 0,
    _('Low'): 1,
    _('Normal'): 4,
    _('High'): 7,
}

del _

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 58846
DEFAULT_HOSTS = {
    'hosts': [(sha(str(time.time())).hexdigest(), DEFAULT_HOST, DEFAULT_PORT, '', '')]
}

# The keys from session statistics for cache status.
DISK_CACHE_KEYS = [
    'disk.num_blocks_read', 'disk.num_blocks_written', 'disk.num_read_ops', 'disk.num_write_ops',
    'disk.num_blocks_cache_hits', 'read_hit_ratio', 'write_hit_ratio', 'disk.disk_blocks_in_use',
    'disk.read_cache_blocks'
]


class TorrentInfo(object):
    """
    Collects information about a torrent file.

    :param filename: The path to the torrent
    :type filename: string

    """
    def __init__(self, filename, filetree=1):
        # Get the torrent data from the torrent file
        try:
            log.debug('Attempting to open %s.', filename)
            with open(filename, 'rb') as _file:
                self.__m_filedata = _file.read()
        except IOError as ex:
            log.warning('Unable to open %s: %s', filename, ex)
            raise ex
        try:
            self.__m_metadata = bencode.bdecode(self.__m_filedata)
        except bencode.BTFailure as ex:
            log.warning('Failed to decode %s: %s', filename, ex)
            raise ex

        self.__m_info_hash = sha(bencode.bencode(self.__m_metadata['info'])).hexdigest()

        # Get encoding from torrent file if available
        self.encoding = None
        if 'encoding' in self.__m_metadata:
            self.encoding = self.__m_metadata['encoding']
        elif 'codepage' in self.__m_metadata:
            self.encoding = str(self.__m_metadata['codepage'])
        if not self.encoding:
            self.encoding = 'UTF-8'

        # Check if 'name.utf-8' is in the torrent and if not try to decode the string
        # using the encoding found.
        if 'name.utf-8' in self.__m_metadata['info']:
            self.__m_name = utf8_encoded(self.__m_metadata['info']['name.utf-8'])
        else:
            self.__m_name = utf8_encoded(self.__m_metadata['info']['name'], self.encoding)

        # Get list of files from torrent info
        paths = {}
        dirs = {}
        if 'files' in self.__m_metadata['info']:
            prefix = ''
            if len(self.__m_metadata['info']['files']) > 1:
                prefix = self.__m_name

            for index, f in enumerate(self.__m_metadata['info']['files']):
                if 'path.utf-8' in f:
                    path = os.path.join(prefix, *f['path.utf-8'])
                    del f['path.utf-8']
                else:
                    path = utf8_encoded(os.path.join(prefix, utf8_encoded(os.path.join(*f['path']),
                                                                          self.encoding)), self.encoding)
                f['path'] = path
                f['index'] = index
                if 'sha1' in f and len(f['sha1']) == 20:
                    f['sha1'] = f['sha1'].encode('hex')
                if 'ed2k' in f and len(f['ed2k']) == 16:
                    f['ed2k'] = f['ed2k'].encode('hex')
                if 'filehash' in f and len(f['filehash']) == 20:
                    f['filehash'] = f['filehash'].encode('hex')
                paths[path] = f
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

                file_tree = FileTree2(paths.keys())
                file_tree.walk(walk)
            else:
                def walk(path, item):
                    if isinstance(item, dict):
                        return item
                    return [paths[path]['index'], paths[path]['length'], True]

                file_tree = FileTree(paths)
                file_tree.walk(walk)
            self.__m_files_tree = file_tree.get_tree()
        else:
            if filetree == 2:
                self.__m_files_tree = {
                    'contents': {
                        self.__m_name: {
                            'type': 'file',
                            'index': 0,
                            'length': self.__m_metadata['info']['length'],
                            'download': True
                        }
                    }
                }
            else:
                self.__m_files_tree = {
                    self.__m_name: (0, self.__m_metadata['info']['length'], True)
                }

        self.__m_files = []
        if 'files' in self.__m_metadata['info']:
            prefix = ''
            if len(self.__m_metadata['info']['files']) > 1:
                prefix = self.__m_name

            for f in self.__m_metadata['info']['files']:
                self.__m_files.append({
                    'path': f['path'],
                    'size': f['length'],
                    'download': True
                })
        else:
            self.__m_files.append({
                'path': self.__m_name,
                'size': self.__m_metadata['info']['length'],
                'download': True
            })

    def as_dict(self, *keys):
        """
        Return the torrent info as a dictionary, only including the passed in
        keys.

        :param keys: a number of key strings
        :type keys: string
        """
        return dict([(key, getattr(self, key)) for key in keys])

    @property
    def name(self):
        """
        The name of the torrent.

        :rtype: string
        """
        return self.__m_name

    @property
    def info_hash(self):
        """
        The torrents info_hash

        :rtype: string
        """
        return self.__m_info_hash

    @property
    def files(self):
        """
        A list of the files that the torrent contains.

        :rtype: list
        """
        return self.__m_files

    @property
    def files_tree(self):
        """
        A dictionary based tree of the files.

        ::

            {
                "some_directory": {
                    "some_file": (index, size, download)
                }
            }

        :rtype: dictionary
        """
        return self.__m_files_tree

    @property
    def metadata(self):
        """
        The torrents metadata.

        :rtype: dictionary
        """
        return self.__m_metadata

    @property
    def filedata(self):
        """
        The torrents file data.  This will be the bencoded dictionary read
        from the torrent file.

        :rtype: string
        """
        return self.__m_filedata


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
                    parent['contents'][directory] = {
                        'type': 'dir',
                        'contents': {}
                    }
                parent = parent['contents'][directory]
            return parent, path

        for path in paths:
            if path[-1] == '/':
                path = path[:-1]
                parent, path = get_parent(path)
                parent['contents'][path] = {
                    'type': 'dir',
                    'contents': {}
                }
            else:
                parent, path = get_parent(path)
                parent['contents'][path] = {
                    'type': 'file'
                }

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
            for path in directory['contents'].keys():
                full_path = os.path.join(parent_path, path).replace('\\', '/')
                if directory['contents'][path]['type'] == 'dir':
                    directory['contents'][path] = callback(
                        full_path, directory['contents'][path]
                        ) or directory['contents'][path]
                    walk(directory['contents'][path], full_path)
                else:
                    directory['contents'][path] = callback(
                        full_path, directory['contents'][path]
                        ) or directory['contents'][path]
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
            for path in directory.keys():
                full_path = os.path.join(parent_path, path)
                if isinstance(directory[path], dict):
                    directory[path] = callback(full_path, directory[path]) or directory[path]
                    walk(directory[path], full_path)
                else:
                    directory[path] = callback(full_path, directory[path]) or directory[path]
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


def get_localhost_auth():
    """
    Grabs the localclient auth line from the 'auth' file and creates a localhost uri

    :returns: with the username and password to login as
    :rtype: tuple
    """
    auth_file = deluge.configmanager.get_config_dir('auth')
    if not os.path.exists(auth_file):
        from deluge.common import create_localclient_account
        create_localclient_account()

    with open(auth_file) as auth:
        for line in auth:
            line = line.strip()
            if line.startswith('#') or not line:
                # This is a comment or blank line
                continue

            lsplit = line.split(':')

            if len(lsplit) == 2:
                username, password = lsplit
            elif len(lsplit) == 3:
                username, password, level = lsplit
            else:
                log.error('Your auth file is malformed: Incorrect number of fields!')
                continue

            if username == 'localclient':
                return (username, password)
