# Taken from http://download.bittorrent.com/dl/BitTorrent-5.3-GPL.tar.gz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Written by Bram Cohen
# Modifications for use in Deluge by Andrew Resch 2008

import os
import os.path
import sys
import time
from hashlib import sha1 as sha

from deluge.bencode import bencode
from deluge.log import LOG as log

ignore = ['core', 'CVS', 'Thumbs.db', 'desktop.ini']

noncharacter_translate = {}
for i in xrange(0xD800, 0xE000):
    noncharacter_translate[i] = ord('-')
for i in xrange(0xFDD0, 0xFDF0):
    noncharacter_translate[i] = ord('-')
for i in (0xFFFE, 0xFFFF):
    noncharacter_translate[i] = ord('-')

def gmtime():
    return time.mktime(time.gmtime())

def get_filesystem_encoding():
    return sys.getfilesystemencoding()

def decode_from_filesystem(path):
    encoding = get_filesystem_encoding()
    if encoding == None:
        assert isinstance(path, unicode), "Path should be unicode not %s" % type(path)
        decoded_path = path
    else:
        assert isinstance(path, str), "Path should be str not %s" % type(path)
        decoded_path = path.decode(encoding)

    return decoded_path

def dummy(*v):
    pass

def make_meta_file(path, url, piece_length, progress=dummy,
                   title=None, comment=None, safe=None, content_type=None,
                   target=None, webseeds=None, name=None, private=False,
                   created_by=None, trackers=None):
    data = {'creation date': int(gmtime())}
    if url:
        data['announce'] = url.strip()
    a, b = os.path.split(path)
    if not target:
        if b == '':
            f = a + '.torrent'
        else:
            f = os.path.join(a, b + '.torrent')
    else:
        f = target
    info = makeinfo(path, piece_length, progress, name, content_type, private)

    #check_info(info)
    h = file(f, 'wb')

    data['info'] = info
    if title:
        data['title'] = title.encode("utf8")
    if comment:
        data['comment'] = comment.encode("utf8")
    if safe:
        data['safe'] = safe.encode("utf8")

    httpseeds = []
    url_list = []

    if webseeds:
        for webseed in webseeds:
            if webseed.endswith(".php"):
                httpseeds.append(webseed)
            else:
                url_list.append(webseed)

    if url_list:
        data['url-list'] = url_list
    if httpseeds:
        data['httpseeds'] = httpseeds
    if created_by:
        data['created by'] = created_by.encode("utf8")

    if trackers and (len(trackers[0]) > 1 or len(trackers) > 1):
        data['announce-list'] = trackers

    data["encoding"] = "UTF-8"

    h.write(bencode(data))
    h.close()

def calcsize(path):
    total = 0
    for s in subfiles(os.path.abspath(path)):
        total += os.path.getsize(s[1])
    return total

def makeinfo(path, piece_length, progress, name = None,
             content_type = None, private=False):  # HEREDAVE. If path is directory,
                                    # how do we assign content type?
    def to_utf8(name):
        if isinstance(name, unicode):
            u = name
        else:
            try:
                u = decode_from_filesystem(name)
            except Exception, e:
                raise Exception('Could not convert file/directory name %r to '
                                  'Unicode. Either the assumed filesystem '
                                  'encoding "%s" is wrong or the filename contains '
                                  'illegal bytes.' % (name, get_filesystem_encoding()))

        if u.translate(noncharacter_translate) != u:
            raise Exception('File/directory name "%s" contains reserved '
                              'unicode values that do not correspond to '
                              'characters.' % name)
        return u.encode('utf-8')
    path = os.path.abspath(path)
    piece_count = 0
    if os.path.isdir(path):
        subs = subfiles(path)
        subs.sort()
        pieces = []
        sh = sha()
        done = 0
        fs = []
        totalsize = 0.0
        totalhashed = 0
        for p, f in subs:
            totalsize += os.path.getsize(f)
        if totalsize >= piece_length:
            import math
            num_pieces = math.ceil(float(totalsize) / float(piece_length))
        else:
            num_pieces = 1

        for p, f in subs:
            pos = 0
            size = os.path.getsize(f)
            p2 = [to_utf8(n) for n in p]
            if content_type:
                fs.append({'length': size, 'path': p2,
                           'content_type' : content_type}) # HEREDAVE. bad for batch!
            else:
                fs.append({'length': size, 'path': p2})
            h = file(f, 'rb')
            while pos < size:
                a = min(size - pos, piece_length - done)
                sh.update(h.read(a))
                done += a
                pos += a
                totalhashed += a

                if done == piece_length:
                    pieces.append(sh.digest())
                    piece_count += 1
                    done = 0
                    sh = sha()
                    progress(piece_count, num_pieces)
            h.close()
        if done > 0:
            pieces.append(sh.digest())
            progress(piece_count, num_pieces)
            
        if name is not None:
            assert isinstance(name, unicode)
            name = to_utf8(name)
        else:
            name = to_utf8(os.path.split(path)[1])

        return {'pieces': ''.join(pieces),
            'piece length': piece_length, 'files': fs,
            'name': name,
            'private': private}
    else:
        size = os.path.getsize(path)
        if size >= piece_length:
            num_pieces = size / piece_length
        else:
            num_pieces = 1

        pieces = []
        p = 0
        h = file(path, 'rb')
        while p < size:
            x = h.read(min(piece_length, size - p))
            pieces.append(sha(x).digest())
            piece_count += 1
            p += piece_length
            if p > size:
                p = size
            progress(piece_count, num_pieces)
        h.close()
        if content_type is not None:
            return {'pieces': ''.join(pieces),
                'piece length': piece_length, 'length': size,
                'name': to_utf8(os.path.split(path)[1]),
                'content_type' : content_type,
                'private': private }
        return {'pieces': ''.join(pieces),
            'piece length': piece_length, 'length': size,
            'name': to_utf8(os.path.split(path)[1]),
            'private': private}

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
