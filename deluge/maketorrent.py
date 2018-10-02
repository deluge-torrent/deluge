# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import division, unicode_literals

import os
from hashlib import sha1 as sha

from deluge.bencode import bencode
from deluge.common import get_path_size, utf8_encode_structure


class InvalidPath(Exception):
    """Raised when an invalid path is supplied."""

    pass


class InvalidPieceSize(Exception):
    """Raised when an invalid piece size is set.

    Note:
        Piece sizes must be multiples of 16KiB.
    """

    pass


class TorrentMetadata(object):
    """This class is used to create .torrent files.

    Examples:

        >>> t = TorrentMetadata()
        >>> t.data_path = '/tmp/torrent'
        >>> t.comment = 'My Test Torrent'
        >>> t.trackers = [['http://tracker.openbittorent.com']]
        >>> t.save('/tmp/test.torrent')

    """

    def __init__(self):
        self.__data_path = None
        self.__piece_size = 0
        self.__comment = ''
        self.__private = False
        self.__trackers = []
        self.__webseeds = []
        self.__pad_files = False

    def save(self, torrent_path, progress=None):
        """Creates and saves the torrent file to `path`.

        Args:
            torrent_path (str): Location to save the torrent file.
            progress(func, optional): The function to be called when a piece is hashed. The
                provided function should be in the format `func(num_completed, num_pieces)`.

        Raises:
            InvalidPath: If the data_path has not been set.

        """
        if not self.data_path:
            raise InvalidPath('Need to set a data_path!')

        torrent = {'info': {}}

        if self.comment:
            torrent['comment'] = self.comment

        if self.private:
            torrent['info']['private'] = True

        if self.trackers:
            torrent['announce'] = self.trackers[0][0]
            torrent['announce-list'] = self.trackers
        else:
            torrent['announce'] = ''

        if self.webseeds:
            httpseeds = []
            webseeds = []
            for w in self.webseeds:
                if w.endswith('.php'):
                    httpseeds.append(w)
                else:
                    webseeds.append(w)

            if httpseeds:
                torrent['httpseeds'] = httpseeds
            if webseeds:
                torrent['url-list'] = webseeds

        datasize = get_path_size(self.data_path)

        if self.piece_size:
            piece_size = self.piece_size * 1024
        else:
            # We need to calculate a piece size
            piece_size = 16384
            while (datasize // piece_size) > 1024 and piece_size < (8192 * 1024):
                piece_size *= 2

        # Calculate the number of pieces we will require for the data
        num_pieces = datasize // piece_size
        if datasize % piece_size:
            num_pieces += 1

        torrent['info']['piece length'] = piece_size
        torrent['info']['name'] = os.path.split(self.data_path)[1]

        # Create the info
        if os.path.isdir(self.data_path):
            files = []
            padding_count = 0
            # Collect a list of file paths and add padding files if necessary
            for (dirpath, dirnames, filenames) in os.walk(self.data_path):
                for index, filename in enumerate(filenames):
                    size = get_path_size(
                        os.path.join(self.data_path, dirpath, filename)
                    )
                    p = dirpath[len(self.data_path) :]
                    p = p.lstrip('/')
                    p = p.split('/')
                    if p[0]:
                        p += [filename]
                    else:
                        p = [filename]
                    files.append((size, p))
                    # Add a padding file if necessary
                    if self.pad_files and (index + 1) < len(filenames):
                        left = size % piece_size
                        if left:
                            p = list(p)
                            p[-1] = '_____padding_file_' + str(padding_count)
                            files.append((piece_size - left, p))
                            padding_count += 1

            # Run the progress function with 0 completed pieces
            if progress:
                progress(0, num_pieces)

            fs = []
            pieces = []
            # Create the piece hashes
            buf = b''
            for size, path in files:
                path = [s.encode('UTF-8') for s in path]
                fs.append({b'length': size, b'path': path})
                if path[-1].startswith(b'_____padding_file_'):
                    buf += b'\0' * size
                    pieces.append(sha(buf).digest())
                    buf = b''
                    fs[-1][b'attr'] = b'p'
                else:
                    with open(
                        os.path.join(self.data_path.encode('utf8'), *path), 'rb'
                    ) as _file:
                        r = _file.read(piece_size - len(buf))
                        while r:
                            buf += r
                            if len(buf) == piece_size:
                                pieces.append(sha(buf).digest())
                                # Run the progress function if necessary
                                if progress:
                                    progress(len(pieces), num_pieces)
                                buf = b''
                            else:
                                break
                            r = _file.read(piece_size - len(buf))
            torrent['info']['files'] = fs
            if buf:
                pieces.append(sha(buf).digest())
                if progress:
                    progress(len(pieces), num_pieces)
                buf = ''

        elif os.path.isfile(self.data_path):
            torrent['info']['length'] = get_path_size(self.data_path)
            pieces = []

            with open(self.data_path, 'rb') as _file:
                r = _file.read(piece_size)
                while r:
                    pieces.append(sha(r).digest())
                    if progress:
                        progress(len(pieces), num_pieces)

                    r = _file.read(piece_size)

        torrent['info']['pieces'] = b''.join(pieces)

        # Write out the torrent file
        with open(torrent_path, 'wb') as _file:
            _file.write(bencode(utf8_encode_structure(torrent)))

    def get_data_path(self):
        """Get the path to the files that the torrent will contain.

        Note:
            It can be either a file or a folder.

        Returns:
            str: The torrent data path, either a file or a folder.

        """
        return self.__data_path

    def set_data_path(self, path):
        """Set the path to the files (data) that the torrent will contain.

        Note:
            This property needs to be set before the torrent file can be created and saved.

        Args:
            path (str): The path to the torrent data and can be either a file or a folder.

        Raises:
            InvalidPath: If the path is not found.

        """
        if os.path.exists(path) and (os.path.isdir(path) or os.path.isfile(path)):
            self.__data_path = os.path.abspath(path)
        else:
            raise InvalidPath('No such file or directory: %s' % path)

    def get_piece_size(self):
        """The size of the pieces.

        Returns:
            int: The piece size in multiples of 16 KiBs.
        """
        return self.__piece_size

    def set_piece_size(self, size):
        """Set piece size.

        Note:
            If no piece size is set, one will be automatically selected to
            produce a torrent with less than 1024 pieces or the smallest possible
            with a 8192KiB piece size.

        Args:
            size (int): The desired piece size in multiples of 16 KiBs.

        Raises:
            InvalidPieceSize: If the piece size is not a valid multiple of 16 KiB.

        """
        if size % 16 and size:
            raise InvalidPieceSize('Piece size must be a multiple of 16 KiB')
        self.__piece_size = size

    def get_comment(self):
        """Get the torrent comment.

        Returns:
            str: An informational string about the torrent.

        """
        return self.__comment

    def set_comment(self, comment):
        """Set the comment for the torrent.

        Args:
            comment (str): An informational string about the torrent.

        """
        self.__comment = comment

    def get_private(self):
        """Get the private flag of the torrent.

        Returns:
            bool: True if private flag has been set, else False.

        """
        return self.__private

    def set_private(self, private):
        """Set the torrent private flag.

        Note:
            Private torrents only announce to trackers and will not use DHT or
            Peer Exchange. See http://bittorrent.org/beps/bep_0027.html

        Args:
            private (bool): True if the torrent is to be private.

        """
        self.__private = private

    def get_trackers(self):
        """Get the announce trackers.

        Note:
            See http://bittorrent.org/beps/bep_0012.html

        Returns:
            list of lists: A list containing a list of trackers.

        """
        return self.__trackers

    def set_trackers(self, trackers):
        """Set the announce trackers.

        Args:
            private (list of lists): A list containing lists of trackers as strings, each list is a tier.

        """
        self.__trackers = trackers

    def get_webseeds(self):
        """Get the webseeds.

        Note:
            The web seeds can either be:
                Hoffman-style: http://bittorrent.org/beps/bep_0017.html
                GetRight-style: http://bittorrent.org/beps/bep_0019.html

            If the url ends in '.php' then it will be considered Hoffman-style, if
            not it will be considered GetRight-style.

        Returns:
            list: The webseeds.

        """
        return self.__webseeds

    def set_webseeds(self, webseeds):
        """Set webseeds.

        Note:
            The web seeds can either be:
                Hoffman-style: http://bittorrent.org/beps/bep_0017.html
                GetRight-style: http://bittorrent.org/beps/bep_0019.html

            If the url ends in '.php' then it will be considered Hoffman-style, if
            not it will be considered GetRight-style.

        Args:
            private (list): The webseeds URLs which can be either Hoffman or GetRight style.

        """
        self.__webseeds = webseeds

    def get_pad_files(self):
        """Get status of padding files for the torrent.

        Returns:
            bool: True if padding files have been enabled to align files on piece boundaries.

        """
        return self.__pad_files

    def set_pad_files(self, pad):
        """Enable padding files for the torrent.

        Args:
            private (bool): True adds padding files to align files on piece boundaries.

        """
        self.__pad_files = pad

    data_path = property(get_data_path, set_data_path)
    piece_size = property(get_piece_size, set_piece_size)
    comment = property(get_comment, set_comment)
    private = property(get_private, set_private)
    trackers = property(get_trackers, set_trackers)
    webseeds = property(get_webseeds, set_webseeds)
    pad_files = property(get_pad_files, set_pad_files)
