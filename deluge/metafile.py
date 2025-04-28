#
# Original file from BitTorrent-5.3-GPL.tar.gz
# Copyright (C) Bram Cohen
#
# Modifications for use in Deluge:
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import copy
import logging
import os.path
import time
from enum import Enum
from hashlib import sha1 as sha
from hashlib import sha256

import deluge.component as component
from deluge.bencode import bencode
from deluge.common import utf8_encode_structure
from deluge.event import CreateTorrentProgressEvent

log = logging.getLogger(__name__)

ignore = ['core', 'CVS', 'Thumbs.db', 'desktop.ini']

noncharacter_translate = {}
for i in range(0xD800, 0xE000):
    noncharacter_translate[i] = ord('-')
for i in range(0xFDD0, 0xFDF0):
    noncharacter_translate[i] = ord('-')
for i in (0xFFFE, 0xFFFF):
    noncharacter_translate[i] = ord('-')


def gmtime():
    return time.mktime(time.gmtime())


def dummy(*v):
    pass


class TorrentFormat(str, Enum):
    V1 = 'v1'
    V2 = 'v2'
    HYBRID = 'hybrid'

    @classmethod
    def _missing_(cls, value):
        if not value:
            return None

        value = value.lower()
        for member in cls:
            if member.value == value:
                return member

    def to_lt_flag(self):
        if self.value == 'v1':
            return 64
        if self.value == 'v2':
            return 32
        return 0

    def includes_v1(self):
        return self == self.__class__.V1 or self == self.__class__.HYBRID

    def includes_v2(self):
        return self == self.__class__.V2 or self == self.__class__.HYBRID


class RemoteFileProgress:
    def __init__(self, session_id):
        self.session_id = session_id

    def __call__(self, piece_count, num_pieces):
        component.get('RPCServer').emit_event_for_session_id(
            self.session_id, CreateTorrentProgressEvent(piece_count, num_pieces)
        )


def make_meta_file_content(
    path,
    url,
    piece_length,
    progress=None,
    title=None,
    comment=None,
    safe=None,
    content_type=None,
    webseeds=None,
    name=None,
    private=False,
    created_by=None,
    trackers=None,
    torrent_format=TorrentFormat.V1,
):
    data = {'creation date': int(gmtime())}
    if url:
        data['announce'] = url.strip()

    if progress is None:
        progress = dummy
        try:
            session_id = component.get('RPCServer').get_session_id()
        except KeyError:
            pass
        else:
            if session_id:
                progress = RemoteFileProgress(session_id)

    info, piece_layers = makeinfo(
        path,
        piece_length,
        progress,
        name,
        content_type,
        private,
        torrent_format,
    )

    # check_info(info)
    data['info'] = info
    if piece_layers is not None:
        data['piece layers'] = piece_layers
    if title:
        data['title'] = title.encode('utf8')
    if comment:
        data['comment'] = comment.encode('utf8')
    if safe:
        data['safe'] = safe.encode('utf8')

    httpseeds = []
    url_list = []

    if webseeds:
        for webseed in webseeds:
            if webseed.endswith('.php'):
                httpseeds.append(webseed)
            else:
                url_list.append(webseed)

    if url_list:
        data['url-list'] = url_list
    if httpseeds:
        data['httpseeds'] = httpseeds
    if created_by:
        data['created by'] = created_by.encode('utf8')

    if trackers and (len(trackers[0]) > 1 or len(trackers) > 1):
        data['announce-list'] = trackers

    data['encoding'] = 'UTF-8'
    return bencode(utf8_encode_structure(data))


def default_meta_file_path(content_path):
    a, b = os.path.split(content_path)
    if b == '':
        f = a + '.torrent'
    else:
        f = os.path.join(a, b + '.torrent')
    return f


def make_meta_file(
    path,
    url,
    piece_length,
    progress=None,
    title=None,
    comment=None,
    safe=None,
    content_type=None,
    target=None,
    webseeds=None,
    name=None,
    private=False,
    created_by=None,
    trackers=None,
):
    if not target:
        target = default_meta_file_path(path)

    file_content = make_meta_file_content(
        path,
        url,
        piece_length,
        progress=progress,
        title=title,
        comment=comment,
        safe=safe,
        content_type=content_type,
        webseeds=webseeds,
        name=name,
        private=private,
        created_by=created_by,
        trackers=trackers,
    )

    with open(target, 'wb') as file_:
        file_.write(file_content)


def calcsize(path):
    total = 0
    for s in subfiles(os.path.abspath(path)):
        total += os.path.getsize(s[1])
    return total


def _next_pow2(num):
    import math

    if not num:
        return 1
    return 2 ** math.ceil(math.log2(num))


def _sha256_merkle_root(leafs, nb_leafs, padding, in_place=True) -> bytes:
    """
    Build the root of the merkle hash tree from the (possibly incomplete) leafs layer.
    If len(leafs) < nb_leafs, it will be padded with the padding repeated as many times
    as needed to have nb_leafs in total.
    """
    if not in_place:
        leafs = copy.copy(leafs)

    while nb_leafs > 1:
        nb_leafs = nb_leafs // 2
        for i in range(nb_leafs):
            node1 = leafs[2 * i] if 2 * i < len(leafs) else padding
            node2 = leafs[2 * i + 1] if 2 * i + 1 < len(leafs) else padding
            h = sha256(node1)
            h.update(node2)
            if i < len(leafs):
                leafs[i] = h.digest()
            else:
                leafs.append(h.digest())
    return leafs[0] if leafs else padding


def _sha256_buffer_blocks(buffer, block_len):
    import math

    nb_blocks = math.ceil(len(buffer) / block_len)
    blocks = [
        sha256(buffer[i * block_len : (i + 1) * block_len]).digest()
        for i in range(nb_blocks)
    ]
    return blocks


def makeinfo_lt(
    path, piece_length, name=None, private=False, torrent_format=TorrentFormat.V1
):
    """
    Make info using via the libtorrent library.
    """
    from deluge._libtorrent import lt

    if not name:
        name = os.path.split(path)[1]

    fs = lt.file_storage()
    if os.path.isfile(path):
        lt.add_files(fs, path)
    else:
        for p, f in subfiles(path):
            fs.add_file(os.path.join(name, *p), os.path.getsize(f))
    torrent = lt.create_torrent(
        fs, piece_size=piece_length, flags=torrent_format.to_lt_flag()
    )

    lt.set_piece_hashes(torrent, os.path.dirname(path))
    torrent.set_priv(private)

    t = torrent.generate()
    info = t[b'info']
    pieces_layers = t.get(b'piece layers', None)

    return info, pieces_layers


def makeinfo(
    path,
    piece_length,
    progress,
    name=None,
    content_type=None,
    private=False,
    torrent_format=TorrentFormat.V1,
):
    # HEREDAVE. If path is directory, how do we assign content type?

    v2_block_len = 2**14  # 16 KiB
    v2_blocks_per_piece = 1
    v2_block_padding = b''
    v2_piece_padding = b''
    if torrent_format.includes_v2():
        if _next_pow2(piece_length) != piece_length or piece_length < v2_block_len:
            raise ValueError(
                'Bittorrent v2 piece size must be a power of 2; and bigger than 16 KiB'
            )

        v2_blocks_per_piece = piece_length // v2_block_len
        v2_block_padding = bytes(32)  # 32 = size of sha256 in bytes
        v2_piece_padding = _sha256_merkle_root(
            [], nb_leafs=v2_blocks_per_piece, padding=v2_block_padding
        )

    path = os.path.abspath(path)
    files = []
    pieces = []
    file_tree = {}
    piece_layers = {}
    if os.path.isdir(path):
        if not name:
            name = os.path.split(path)[1]
        subs = subfiles(path)
        if torrent_format.includes_v2():
            subs = sorted(subs)
        length = None
        totalsize = 0.0
        for p, f in subs:
            totalsize += os.path.getsize(f)
    else:
        name = os.path.split(path)[1]
        subs = [([name], path)]
        length = os.path.getsize(path)
        totalsize = length
    is_multi_file = len(subs) > 1
    sh = sha()
    done = 0
    totalhashed = 0

    next_progress_event = piece_length
    for p, f in subs:
        file_pieces_v2 = []
        pos = 0
        size = os.path.getsize(f)
        p2 = [n.encode('utf8') for n in p]
        if content_type:
            files.append(
                {b'length': size, b'path': p2, b'content_type': content_type}
            )  # HEREDAVE. bad for batch!
        else:
            files.append({b'length': size, b'path': p2})
        with open(f, 'rb') as file_:
            while pos < size:
                to_read = min(size - pos, piece_length)
                buffer = memoryview(file_.read(to_read))
                pos += to_read

                if torrent_format.includes_v1():
                    a = piece_length - done
                    for sub_buffer in (buffer[:a], buffer[a:]):
                        if sub_buffer:
                            sh.update(sub_buffer)
                            done += len(sub_buffer)

                            if done == piece_length:
                                pieces.append(sh.digest())
                                done = 0
                                sh = sha()
                if torrent_format.includes_v2():
                    block_hashes = _sha256_buffer_blocks(buffer, v2_block_len)
                    num_leafs = v2_blocks_per_piece
                    if size <= piece_length:
                        # The special case when the file is smaller than a piece: only pad till the next power of 2
                        num_leafs = _next_pow2(len(block_hashes))
                    root = _sha256_merkle_root(
                        block_hashes, num_leafs, v2_block_padding, in_place=True
                    )
                    file_pieces_v2.append(root)

                totalhashed += to_read
                if totalhashed >= next_progress_event:
                    next_progress_event = totalhashed + piece_length
                    progress(totalhashed, totalsize)

        if torrent_format == TorrentFormat.HYBRID and is_multi_file and done > 0:
            # Add padding file to force piece-alignment
            padding = piece_length - done
            sh.update(bytes(padding))
            files.append(
                {
                    b'length': padding,
                    b'attr': b'p',
                    b'path': [b'.pad', str(padding).encode()],
                }
            )
            pieces.append(sh.digest())
            done = 0
            sh = sha()

        if torrent_format.includes_v2():
            # add file to the `file tree` and, if needed, to the `piece layers` structures
            pieces_root = _sha256_merkle_root(
                file_pieces_v2,
                _next_pow2(len(file_pieces_v2)),
                v2_piece_padding,
                in_place=False,
            )
            dst_directory = file_tree
            for directory in p2[:-1]:
                dst_directory = dst_directory.setdefault(directory, {})
            dst_directory[p2[-1]] = {
                b'': {
                    b'length': size,
                    b'pieces root': pieces_root,
                }
            }
            if len(file_pieces_v2) > 1:
                piece_layers[pieces_root] = b''.join(file_pieces_v2)

    if done > 0:
        pieces.append(sh.digest())
    progress(totalsize, totalsize)

    info = {
        b'piece length': piece_length,
        b'name': name.encode('utf8'),
    }
    if private:
        info[b'private'] = 1
    if content_type:
        info[b'content_type'] = content_type
    if torrent_format.includes_v1():
        info[b'pieces'] = b''.join(pieces)
        if is_multi_file:
            info[b'files'] = files
        else:
            info[b'length'] = length
    if torrent_format.includes_v2():
        info.update(
            {
                b'meta version': 2,
                b'file tree': file_tree,
            }
        )
    return info, piece_layers if torrent_format.includes_v2() else None


def subfiles(d):
    r = []
    stack = [([], d)]
    while stack:
        p, n = stack.pop()
        if os.path.isdir(n):
            for s in os.listdir(n):
                if s not in ignore and not s.startswith('.'):
                    stack.append((p + [s], os.path.join(n, s)))
        else:
            r.append((p, n))
    return r
