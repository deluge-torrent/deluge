# -*- coding: utf-8 -*-
#
# deluge/ui/common.py
#
# Copyright (C) Damien Churchill 2008 <damoxc@gmail.com>
# Copyright (C) Andrew Resch 2009 <andrewresch@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#

import os
import sys
import urlparse

try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha

from deluge import bencode
from deluge.log import LOG as log
import deluge.configmanager

def decode_string(s, encoding="utf8"):
    """
    Decodes a string and re-encodes it in utf8.  If it cannot decode using
    `:param:encoding` then it will try to detect the string encoding and
    decode it.

    :param s: str to decode
    :param encoding: str, the encoding to use in the decoding

    """

    try:
        s = s.decode(encoding).encode("utf8")
    except UnicodeDecodeError:
        try:
            import chardet
        except ImportError:
            s = s.decode(encoding, "replace").encode("utf8")
        else:
            s = s.decode(chardet.detect(s)["encoding"]).encode("utf8")
    return s

class TorrentInfo(object):
    def __init__(self, filename):
        # Get the torrent data from the torrent file
        try:
            log.debug("Attempting to open %s.", filename)
            self.__m_metadata = bencode.bdecode(open(filename, "rb").read())
        except Exception, e:
            log.warning("Unable to open %s: %s", filename, e)
            raise e

        self.__m_info_hash = sha(bencode.bencode(self.__m_metadata["info"])).hexdigest()

        # Get encoding from torrent file if available
        self.encoding = "UTF-8"
        if "encoding" in self.__m_metadata:
            self.encoding = self.__m_metadata["encoding"]
        elif "codepage" in self.__m_metadata:
            self.encoding = str(self.__m_metadata["codepage"])

        # We try to decode based on the encoding found and if we can't, we try
        # to detect the encoding and decode that
        self.__m_name = decode_string(self.__m_metadata["info"]["name"], self.encoding)

        # Get list of files from torrent info
        paths = {}
        if self.__m_metadata["info"].has_key("files"):
            prefix = ""
            if len(self.__m_metadata["info"]["files"]) > 1:
                prefix = self.__m_name

            for index, f in enumerate(self.__m_metadata["info"]["files"]):
                path = decode_string(os.path.join(prefix, *f["path"]))
                f["index"] = index
                paths[path] = f

            def walk(path, item):
                if type(item) is dict:
                    return item
                return [paths[path]['index'], paths[path]['length'], True]

            file_tree = FileTree(paths)
            file_tree.walk(walk)
            self.__m_files_tree = file_tree.get_tree()
        else:
            self.__m_files_tree = {
                self.__m_name: (self.__m_metadata["info"]["length"], True)
            }

        self.__m_files = []
        if self.__m_metadata["info"].has_key("files"):
            prefix = ""
            if len(self.__m_metadata["info"]["files"]) > 1:
                prefix = self.__m_name

            for f in self.__m_metadata["info"]["files"]:
                self.__m_files.append({
                    'path': decode_string(os.path.join(prefix, *f["path"])),
                    'size': f["length"],
                    'download': True
                })
        else:
            self.__m_files.append({
                "path": self.__m_name,
                "size": self.__m_metadata["info"]["length"],
                "download": True
        })

    def as_dict(self, *keys):
        """
        Return the torrent info as a dictionary, only including the passed in
        keys.

        :param *keys: str, a number of key strings
        """
        return dict([(key, getattr(self, key)) for key in keys])

    @property
    def name(self):
        return self.__m_name

    @property
    def info_hash(self):
        return self.__m_info_hash

    @property
    def files(self):
        return self.__m_files

    @property
    def files_tree(self):
        return self.__m_files_tree

    @property
    def metadata(self):
        return self.__m_metadata

class FileTree(object):
    def __init__(self, paths):
        """
        Convert a list of paths in a file tree.

        :param paths: list, The paths to be converted.
        """
        self.tree = {}

        def get_parent(path):
            parent = self.tree
            while "/" in path:
                directory, path = path.split("/", 1)
                child = parent.get(directory)
                if child is None:
                    parent[directory] = {}
                parent = parent[directory]
            return parent, path

        for path in paths:
            if path[-1] == "/":
                path = path[:-1]
                parent, path = get_parent(path)
                parent[path] = {}
            else:
                parent, path = get_parent(path)
                parent[path] = []

    def get_tree(self):
        """
        Return the tree, after first converting all file lists to a tuple.

        :returns: dict, the file tree.
        """
        def to_tuple(path, item):
            if type(item) is dict:
                return item
            return tuple(item)
        self.walk(to_tuple)
        return self.tree

    def walk(self, callback):
        """
        Walk through the file tree calling the callback function on each item
        contained.

        :param callback: function, The function to be used as a callback, it
            should have the signature func(item, path) where item is a `tuple`
            for a file and `dict` for a directory.
        """
        def walk(directory, parent_path):
            for path in directory.keys():
                full_path = os.path.join(parent_path, path)
                if type(directory[path]) is dict:
                    directory[path] = callback(full_path, directory[path]) or \
                             directory[path]
                    walk(directory[path], full_path)
                else:
                    directory[path] = callback(full_path, directory[path]) or \
                             directory[path]
        walk(self.tree, "")

    def __str__(self):
        lines = []
        def write(path, item):
            depth = path.count("/")
            path = os.path.basename(path)
            path = type(item) is dict and path + "/" or path
            lines.append("  " * depth + path)
        self.walk(write)
        return "\n".join(lines)

def get_localhost_auth():
    """
    Grabs the localclient auth line from the 'auth' file and creates a localhost uri

    :returns: tuple, with the username and password to login as
    """
    auth_file = deluge.configmanager.get_config_dir("auth")
    if os.path.exists(auth_file):
        for line in open(auth_file):
            if line.startswith("#"):
                # This is a comment line
                continue
            try:
                lsplit = line.split(":")
            except Exception, e:
                log.error("Your auth file is malformed: %s", e)
                continue

            if len(lsplit) == 2:
                username, password = lsplit
            elif len(lsplit) == 3:
                username, password, level = lsplit
            else:
                log.error("Your auth file is malformed: Incorrect number of fields!")
                continue

            if username == "localclient":
                return (username, password)
    return ("", "")
