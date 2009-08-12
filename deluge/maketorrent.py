#
# maketorrent.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
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
#

import sys
import os
from hashlib import sha1 as sha

from deluge.common import get_path_size
from deluge.bencode import bencode, bdecode

class InvalidPath(Exception):
    """
    Raised when an invalid path is supplied
    """
    pass

class InvalidPieceSize(Exception):
    """
    Raised when an invalid piece size is set.  Piece sizes must be multiples of
    16KiB.
    """
    pass
    
class TorrentMetadata(object):
    """
    This class is used to create .torrent files.
    
    *** Usage ***
    
    >>> t = TorrentMetadata()
    >>> t.data_path = "/tmp/torrent"
    >>> t.comment = "My Test Torrent"
    >>> t.trackers = [["http://tracker.openbittorent.com"]]
    >>> t.save("/tmp/test.torrent")
    
    """
    def __init__(self):
        self.__data_path = None
        self.__piece_size = 0
        self.__comment = ""
        self.__private = False
        self.__trackers = []
        self.__web_seeds = []
        self.__pad_files = False

    def save(self, torrent_path, progress=None):
        """
        Creates and saves the torrent file to `path`.
        
        :param torrent_path: where to save the torrent file
        :type torrent_path: string
        
        :param progress: a function to be called when a piece is hashed
        :type progress: function(num_completed, num_pieces)
        
        :raises InvalidPath: if the data_path has not been set
        
        """
        if not self.data_path:
            raise InvalidPath("Need to set a data_path!")

        torrent = {
            "info": {}
            }
            
        if self.comment:
            torrent["comment"] = self.comment.encode("UTF-8")
        
        if self.private:
            torrent["info"]["private"] = True
        
        if self.trackers:
            torrent["announce"] = self.trackers[0][0]
            torrent["announce-list"] = self.trackers
        else:
            torrent["announce"] = ""
        
        if self.webseeds:
            httpseeds = []
            webseeds = []
            for w in self.webseeds:
                if w.endswith(".php"):
                    httpseeds.append(w)
                else:
                    webseeds.append(w)

            if httpseeds:
                torrent["httpseeds"] = httpseeds
            if webseeds:
                torrent["url-list"] = webseeds
        
        datasize = get_path_size(self.data_path)

        if not self.piece_size:
            # We need to calculate a piece size
            psize = 16384
            while (datasize / psize) > 1024:
                psize *= 2
            
            self.piece_size = psize

        # Calculate the number of pieces we will require for the data
        num_pieces = datasize / self.piece_size
        torrent["info"]["piece length"] = self.piece_size
        
        # Create the info
        if os.path.isdir(self.data_path):
            torrent["info"]["name"] = os.path.split(self.data_path)[1]
            files = []
            padding_count = 0
            # Collect a list of file paths and add padding files if necessary
            for (dirpath, dirnames, filenames) in os.walk(self.data_path):
                for index, filename in enumerate(filenames):
                    size = get_path_size(os.path.join(self.data_path, dirpath, filename))
                    p = dirpath.lstrip(self.data_path)
                    p = p.split("/")
                    if p[0]:
                        p += [filename]
                    else:
                        p = [filename]
                    files.append((size, p))
                    # Add a padding file if necessary
                    if self.pad_files and (index + 1) < len(filenames):
                        left = size % self.piece_size
                        if left:
                            p = list(p)
                            p[-1] = "_____padding_file_" + str(padding_count)
                            files.append((self.piece_size - left, p))
                            padding_count += 1
            

            # Run the progress function with 0 completed pieces
            if progress:
                progress(0, num_pieces)

            fs = []
            pieces = []
            # Create the piece hashes
            buf = ""
            for size, path in files:
                path = [s.decode(sys.getfilesystemencoding()).encode("UTF-8") for s in path]
                fs.append({"length": size, "path": path})
                if path[-1].startswith("_____padding_file_"):
                    buf += "\0" * size
                    pieces.append(sha(buf).digest())
                    buf = ""
                    fs[-1]["attr"] = "p"
                else:
                    fd = open(os.path.join(self.data_path, *path), "rb")
                    r = fd.read(self.piece_size - len(buf))
                    while r:
                        buf += r
                        if len(buf) == self.piece_size:
                            pieces.append(sha(buf).digest())
                            # Run the progress function if necessary
                            if progress:
                                progress(len(pieces), num_pieces)
                            buf = ""
                        else:
                            break
                        r = fd.read(self.piece_size - len(buf))
                    fd.close()

            if buf:
                pieces.append(sha(buf).digest())
                if progress:
                    progress(len(pieces), num_pieces)
                buf = ""
            
            torrent["info"]["pieces"] = "".join(pieces)
            torrent["info"]["files"] = fs

        elif os.path.isfile(self.data_path):
            torrent["info"]["name"] = os.path.split(self.data_path)[1]
            torrent["info"]["length"] = get_path_size(self.data_path)
            pieces = []
            
            fd = open(self.data_path, "rb")      
            r = fd.read(self.piece_size)
            while r:
                pieces.append(sha(r).digest())
                if progress:
                    progress(len(pieces), num_pieces)

                r = fd.read(self.piece_size)
            
            torrent["info"]["pieces"] = "".join(pieces)
        
        # Write out the torrent file
        open(torrent_path, "wb").write(bencode(torrent))
        
    @property
    def data_path(self):
        """
        The path to the files that the torrent will contain.  It can be either
        a file or a folder.  This property needs to be set before the torrent
        file can be created and saved.
        """
        return self.__data_path
    
    @data_path.setter
    def data_path(self, path):
        """
        :param path: the path to the data
        :type path: string
        
        :raises InvalidPath: if the path is not found
        
        """
        if os.path.exists(path) and (os.path.isdir(path) or os.path.isfile(path)):
            self.__data_path = path
        else:
            raise InvalidPath("No such file or directory: %s" % path)

    @property
    def piece_size(self):
        """
        The size of pieces in bytes.  The size must be a multiple of 16KiB.
        If you don't set a piece size, one will be automatically selected to
        produce a torrent with less than 1024 pieces.
        
        """
        return self.__piece_size
    
    @piece_size.setter
    def piece_size(self, size):
        """
        :param size: the desired piece size in bytes
        
        :raises InvalidPieceSize: if the piece size is not a multiple of 16KiB
        
        """
        if size % 16384 and size:
            raise InvalidPieceSize("Piece size must be a multiple of 16384")
        self.__piece_size = size
        
    @property
    def comment(self):
        """
        Comment is some extra info to be stored in the torrent.  This is
        typically an informational string.
        """
        return self.__comment
    
    @comment.setter
    def comment(self, comment):
        """
        :param comment: an informational string
        :type comment: string
        """
        self.__comment = comment
    
    @property
    def private(self):
        """
        Private torrents only announce to the tracker and will not use DHT or
        Peer Exchange.
        
        See: http://bittorrent.org/beps/bep_0027.html
        
        """
        return self.__private
    
    @private.setter
    def private(self, private):
        """
        :param private: True if the torrent is to be private
        :type private: bool
        """
        self.__private = private
    
    @property
    def trackers(self):
        """
        The announce trackers is a list of lists.
        
        See: http://bittorrent.org/beps/bep_0012.html
        
        """
        return self.__trackers
    
    @trackers.setter
    def trackers(self, trackers):
        """
        :param trackers: a list of lists of trackers, each list is a tier
        :type trackers: list of list of strings
        """
        self.__trackers = trackers

    @property
    def webseeds(self):
        """
        The web seeds can either be:
        Hoffman-style: http://bittorrent.org/beps/bep_0017.html
        or,
        GetRight-style: http://bittorrent.org/beps/bep_0019.html
        
        If the url ends in '.php' then it will be considered Hoffman-style, if
        not it will be considered GetRight-style.
        """
        return self.__web_seeds
    
    @webseeds.setter
    def webseeds(self, webseeds):
        """
        :param webseeds: the webseeds which can be either Hoffman or GetRight style
        :type webseeds: list of urls
        """
        self.__webseeds = webseeds

    @property
    def pad_files(self):
        """
        If this is True, padding files will be added to align files on piece
        boundaries.
        """
        return self.__pad_files
    
    @pad_files.setter
    def pad_files(self, pad):
        """
        :param pad: set True to align files on piece boundaries
        :type pad: bool
        """
        self.__pad_files = pad

