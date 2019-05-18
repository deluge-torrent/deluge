# The contents of this file are subject to the Python Software Foundation
# License Version 2.3 (the License).  You may not copy or use this file, in
# either source code or executable form, except in compliance with the License.
# You may obtain a copy of the License at http://www.python.org/license.
#
# Software distributed under the License is distributed on an AS IS basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied.  See the License
# for the specific language governing rights and limitations under the
# License.

# Written by Petru Paler
# Updated by Calum Lind to support both Python 2 and Python 3.

from __future__ import unicode_literals

from sys import version_info

PY2 = version_info.major == 2


class BTFailure(Exception):
    pass


DICT_DELIM = b'd'
END_DELIM = b'e'
INT_DELIM = b'i'
LIST_DELIM = b'l'
BYTE_SEP = b':'


def decode_int(x, f):
    f += 1
    newf = x.index(END_DELIM, f)
    n = int(x[f:newf])
    if x[f : f + 1] == b'-' and x[f + 1 : f + 2] == b'0':
        raise ValueError
    elif x[f : f + 1] == b'0' and newf != f + 1:
        raise ValueError
    return (n, newf + 1)


def decode_string(x, f):
    colon = x.index(BYTE_SEP, f)
    n = int(x[f:colon])
    if x[f : f + 1] == b'0' and colon != f + 1:
        raise ValueError
    colon += 1
    return (x[colon : colon + n], colon + n)


def decode_list(x, f):
    r, f = [], f + 1
    while x[f : f + 1] != END_DELIM:
        v, f = decode_func[x[f : f + 1]](x, f)
        r.append(v)
    return (r, f + 1)


def decode_dict(x, f):
    r, f = {}, f + 1
    while x[f : f + 1] != END_DELIM:
        k, f = decode_string(x, f)
        r[k], f = decode_func[x[f : f + 1]](x, f)
    return (r, f + 1)


decode_func = {}
decode_func[LIST_DELIM] = decode_list
decode_func[DICT_DELIM] = decode_dict
decode_func[INT_DELIM] = decode_int
decode_func[b'0'] = decode_string
decode_func[b'1'] = decode_string
decode_func[b'2'] = decode_string
decode_func[b'3'] = decode_string
decode_func[b'4'] = decode_string
decode_func[b'5'] = decode_string
decode_func[b'6'] = decode_string
decode_func[b'7'] = decode_string
decode_func[b'8'] = decode_string
decode_func[b'9'] = decode_string


def bdecode(x):
    try:
        r, __ = decode_func[x[0:1]](x, 0)
    except (LookupError, TypeError, ValueError):
        raise BTFailure('Not a valid bencoded string')
    else:
        return r


class Bencached(object):

    __slots__ = ['bencoded']

    def __init__(self, s):
        self.bencoded = s


def encode_bencached(x, r):
    r.append(x.bencoded)


def encode_int(x, r):
    r.extend((INT_DELIM, str(x).encode('utf8'), END_DELIM))


def encode_bool(x, r):
    encode_int(1 if x else 0, r)


def encode_string(x, r):
    encode_bytes(x.encode('utf8'), r)


def encode_bytes(x, r):
    r.extend((str(len(x)).encode('utf8'), BYTE_SEP, x))


def encode_list(x, r):
    r.append(LIST_DELIM)
    for i in x:
        encode_func[type(i)](i, r)
    r.append(END_DELIM)


def encode_dict(x, r):
    r.append(DICT_DELIM)
    for k, v in sorted(x.items()):
        try:
            k = k.encode('utf8')
        except AttributeError:
            pass
        r.extend((str(len(k)).encode('utf8'), BYTE_SEP, k))
        encode_func[type(v)](v, r)
    r.append(END_DELIM)


encode_func = {}
encode_func[Bencached] = encode_bencached
encode_func[int] = encode_int
encode_func[list] = encode_list
encode_func[tuple] = encode_list
encode_func[dict] = encode_dict
encode_func[bool] = encode_bool
encode_func[str] = encode_string
encode_func[bytes] = encode_bytes
if PY2:
    encode_func[long] = encode_int  # noqa: F821
    encode_func[str] = encode_bytes
    encode_func[unicode] = encode_string  # noqa: F821


def bencode(x):
    r = []
    encode_func[type(x)](x, r)
    return b''.join(r)
