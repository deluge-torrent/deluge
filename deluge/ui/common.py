#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# deluge/ui/common.py
#
# Copyright (C) Damien Churchill 2008 <damoxc@gmail.com>
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
from sha import sha
import urlparse

from deluge import bencode
from deluge.log import LOG as log
import deluge.configmanager

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

        # Get list of files from torrent info
        self.__m_files = []
        if self.__m_metadata["info"].has_key("files"):
            prefix = ""
            if len(self.__m_metadata["info"]["files"]) > 1:
                prefix = self.__m_metadata["info"]["name"]

            for f in self.__m_metadata["info"]["files"]:
                self.__m_files.append({
                    'path': os.path.join(prefix, *f["path"]),
                    'size': f["length"],
                    'download': True
                })
        else:
            self.__m_files.append({
                "path": self.__m_metadata["info"]["name"],
                "size": self.__m_metadata["info"]["length"],
                "download": True
        })

    @property
    def name(self):
        return self.__m_metadata["info"]["name"]

    @property
    def info_hash(self):
        return self.__m_info_hash

    @property
    def files(self):
        return self.__m_files

    @property
    def metadata(self):
        return self.__m_metadata

def get_torrent_info(filename):
    """
    Return the metadata of a torrent file
    """

    # Get the torrent data from the torrent file
    try:
        log.debug("Attempting to open %s.", filename)
        metadata = bencode.bdecode(open(filename, "rb").read())
    except Exception, e:
        log.warning("Unable to open %s: %s", filename, e)

    info_hash = sha(bencode.bencode(metadata["info"])).hexdigest()

    # Get list of files from torrent info
    files = []
    if metadata["info"].has_key("files"):
        prefix = ""
        if len(metadata["info"]["files"]) > 1:
            prefix = metadata["info"]["name"]

        for f in metadata["info"]["files"]:
            files.append({
                'path': os.path.join(prefix, *f["path"]),
                'size': f["length"],
                'download': True
            })
    else:
        files.append({
            "path": metadata["info"]["name"],
            "size": metadata["info"]["length"],
            "download": True
        })

    return {
        "filename": filename,
        "name": metadata["info"]["name"],
        "files": files,
        "info_hash": info_hash
    }

def get_localhost_auth_uri(uri):
    """
    Grabs the localclient auth line from the 'auth' file and creates a localhost uri

    :param uri: the uri to add the authentication info to
    :returns: a localhost uri containing authentication information or None if the information is not available
    """
    auth_file = deluge.configmanager.get_config_dir("auth")
    if os.path.exists(auth_file):
        u = urlparse.urlsplit(uri)
        for line in open(auth_file):
            try:
                username, password = line.strip().split(":")
            except ValueError:
                continue

            if username == "localclient":
                # We use '127.0.0.1' in place of 'localhost' just incase this isn't defined properly
                hostname = u.hostname.replace("localhost", "127.0.0.1")
                return u.scheme + "://" + username + ":" + password + "@" + hostname + ":" + str(u.port)
    return None
