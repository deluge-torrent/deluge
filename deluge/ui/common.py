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

import logging
import os
from hashlib import sha1 as sha

import deluge.configmanager
from deluge import bencode
from deluge.common import path_join, utf8_encoded

log = logging.getLogger(__name__)


# Dummy tranlation dict so Torrent states text is available for Translators
# All entries in deluge.common.TORRENT_STATE should be here. It does not need importing
# as the string matches the translation text so using the _() function is enough.
def _(message):
    return message
STATE_TRANSLATION = {
    "All": _("All"),
    "Active": _("Active"),
    "Allocating": _("Allocating"),
    "Checking": _("Checking"),
    "Downloading": _("Downloading"),
    "Seeding": _("Seeding"),
    "Paused": _("Paused"),
    "Checking": _("Checking"),
    "Queued": _("Queued"),
    "Error": _("Error"),
}

TRACKER_STATUS_TRANSLATION = {
    "Error": _("Error"),
    "Warning": _("Warning"),
    "Announce OK": _("Announce OK"),
    "Announce Sent": _("Announce Sent")
}
del _


class TorrentInfo(object):
    """
    Collects information about a torrent file.

    :param filename: The path to the torrent
    :type filename: string

    """
    def __init__(self, filename, filetree=1):
        # Get the torrent data from the torrent file
        try:
            log.debug("Attempting to open %s.", filename)
            self.__m_filedata = open(filename, "rb").read()
            self.__m_metadata = bencode.bdecode(self.__m_filedata)
        except Exception as ex:
            log.warning("Unable to open %s: %s", filename, ex)
            raise ex

        self.__m_info_hash = sha(bencode.bencode(self.__m_metadata["info"])).hexdigest()

        # Get encoding from torrent file if available
        self.encoding = None
        if "encoding" in self.__m_metadata:
            self.encoding = self.__m_metadata["encoding"]
        elif "codepage" in self.__m_metadata:
            self.encoding = str(self.__m_metadata["codepage"])
        if not self.encoding:
            self.encoding = "UTF-8"

        # Check if 'name.utf-8' is in the torrent and if not try to decode the string
        # using the encoding found.
        if "name.utf-8" in self.__m_metadata["info"]:
            self.__m_name = utf8_encoded(self.__m_metadata["info"]["name.utf-8"])
        else:
            self.__m_name = utf8_encoded(self.__m_metadata["info"]["name"], self.encoding)

        # Get list of files from torrent info
        paths = {}
        dirs = {}
        if "files" in self.__m_metadata["info"]:
            prefix = ""
            if len(self.__m_metadata["info"]["files"]) > 1:
                prefix = self.__m_name

            for index, f in enumerate(self.__m_metadata["info"]["files"]):
                if "path.utf-8" in f:
                    path = os.path.join(prefix, *f["path.utf-8"])
                    del f["path.utf-8"]
                else:
                    path = utf8_encoded(os.path.join(prefix, utf8_encoded(os.path.join(*f["path"]),
                                                                          self.encoding)), self.encoding)
                f["path"] = path
                f["index"] = index
                if "sha1" in f and len(f["sha1"]) == 20:
                        f["sha1"] = f["sha1"].encode('hex')
                if "ed2k" in f and len(f["ed2k"]) == 16:
                        f["ed2k"] = f["ed2k"].encode('hex')
                paths[path] = f
                dirname = os.path.dirname(path)
                while dirname:
                    dirinfo = dirs.setdefault(dirname, {})
                    dirinfo["length"] = dirinfo.get("length", 0) + f["length"]
                    dirname = os.path.dirname(dirname)

            if filetree == 2:
                def walk(path, item):
                    if item["type"] == "dir":
                        item.update(dirs[path])
                    else:
                        item.update(paths[path])
                    item["download"] = True

                file_tree = FileTree2(paths.keys())
                file_tree.walk(walk)
            else:
                def walk(path, item):
                    if type(item) is dict:
                        return item
                    return [paths[path]["index"], paths[path]["length"], True]

                file_tree = FileTree(paths)
                file_tree.walk(walk)
            self.__m_files_tree = file_tree.get_tree()
        else:
            if filetree == 2:
                self.__m_files_tree = {
                    "contents": {
                        self.__m_name: {
                            "type": "file",
                            "index": 0,
                            "length": self.__m_metadata["info"]["length"],
                            "download": True
                        }
                    }
                }
            else:
                self.__m_files_tree = {
                    self.__m_name: (0, self.__m_metadata["info"]["length"], True)
                }

        self.__m_files = []
        if "files" in self.__m_metadata["info"]:
            prefix = ""
            if len(self.__m_metadata["info"]["files"]) > 1:
                prefix = self.__m_name

            for f in self.__m_metadata["info"]["files"]:
                self.__m_files.append({
                    'path': f["path"],
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
        self.tree = {"contents": {}, "type": "dir"}

        def get_parent(path):
            parent = self.tree
            while "/" in path:
                directory, path = path.split("/", 1)
                child = parent["contents"].get(directory)
                if child is None:
                    parent["contents"][directory] = {
                        "type": "dir",
                        "contents": {}
                    }
                parent = parent["contents"][directory]
            return parent, path

        for path in paths:
            if path[-1] == "/":
                path = path[:-1]
                parent, path = get_parent(path)
                parent["contents"][path] = {
                    "type": "dir",
                    "contents": {}
                }
            else:
                parent, path = get_parent(path)
                parent["contents"][path] = {
                    "type": "file"
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
            for path in directory["contents"].keys():
                full_path = path_join(parent_path, path)
                if directory["contents"][path]["type"] == "dir":
                    directory["contents"][path] = callback(full_path, directory["contents"][path]
                                                           ) or directory["contents"][path]
                    walk(directory["contents"][path], full_path)
                else:
                    directory["contents"][path] = callback(full_path, directory["contents"][path]
                                                           ) or directory["contents"][path]
        walk(self.tree, "")

    def __str__(self):
        lines = []

        def write(path, item):
            depth = path.count("/")
            path = os.path.basename(path)
            path = path + "/" if item["type"] == "dir" else path
            lines.append("  " * depth + path)
        self.walk(write)
        return "\n".join(lines)


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

        :returns: the file tree.
        :rtype: dictionary
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

        :param callback: The function to be used as a callback, it should have
            the signature func(item, path) where item is a `tuple` for a file
            and `dict` for a directory.
        :type callback: function
        """
        def walk(directory, parent_path):
            for path in directory.keys():
                full_path = os.path.join(parent_path, path)
                if type(directory[path]) is dict:
                    directory[path] = callback(full_path, directory[path]) or directory[path]
                    walk(directory[path], full_path)
                else:
                    directory[path] = callback(full_path, directory[path]) or directory[path]
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

    :returns: with the username and password to login as
    :rtype: tuple
    """
    auth_file = deluge.configmanager.get_config_dir("auth")
    if not os.path.exists(auth_file):
        from deluge.common import create_localclient_account
        create_localclient_account()

    with open(auth_file) as auth:
        for line in auth:
            if line.startswith("#"):
                # This is a comment line
                continue

            lsplit = line.strip().split(":")

            if len(lsplit) == 2:
                username, password = lsplit
            elif len(lsplit) == 3:
                username, password, level = lsplit
            else:
                log.error("Your auth file is malformed: Incorrect number of fields!")
                continue

            if username == "localclient":
                return (username, password)
