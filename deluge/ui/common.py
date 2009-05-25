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
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import os
try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha
import urlparse

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

        # Check if 'name.utf-8' is in the torrent and if not try to decode the string
        # using the encoding found.
        if "name.utf-8" in self.__m_metadata["info"]:
            self.__m_name = decode_string(self.__m_metadata["info"]["name.utf-8"])
        else:
            self.__m_name = decode_string(self.__m_metadata["info"]["name"], self.encoding)

        # Get list of files from torrent info
        self.__m_files = []
        if self.__m_metadata["info"].has_key("files"):
            prefix = ""
            if len(self.__m_metadata["info"]["files"]) > 1:
                prefix = self.__m_name

            for f in self.__m_metadata["info"]["files"]:
                self.__m_files.append({
                    'path': decode_string(os.path.join(prefix, decode_string(os.path.join(*f["path"]), self.encoding)), self.encoding),
                    'size': f["length"],
                    'download': True
                })
        else:
            self.__m_files.append({
                "path": self.__m_name,
                "size": self.__m_metadata["info"]["length"],
                "download": True
        })

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
    u = urlparse.urlsplit(uri)
    # If there is already a username in this URI, let's just return it since
    # the user has provided credentials.
    if u.username:
        return uri

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
