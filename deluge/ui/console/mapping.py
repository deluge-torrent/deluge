#!/usr/bin/env python
#
# mapping.py
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
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
from deluge.ui.client import aclient as client
from deluge.ui.console.main import match_torrents
import re
import logging

_idregex = re.compile(r'^[0-9a-f]{40}$')

_mapping = {}

def _arg_is_id(arg):
    return bool(_idregex.match(arg))

def get_names(torrents):
    global names
    names = []
    def _got_torrents_status(states):
        try:
            names.extend(list([ (tid, state['name']) for (tid, state) in states.items() ]))
        except Exception, e:
            print e

    client.get_torrents_status(_got_torrents_status, {'id':torrents}, ['name'])
    client.force_call()
    return names

def rehash():
    global _mapping
    torrents = match_torrents()
    names = get_names(torrents)
    _mapping = dict([(x[1],x[0]) for x in names])
    logging.debug('rehashed torrent name->id mapping')

def to_ids(args):
    res = []
    rehashed = False
    for i in args:
        if _arg_is_id(i):
            res.append(i)
        else:
            if i in _mapping:
                res.append(_mapping[i])
            elif not rehashed:
                rehash()
                if i in _mapping:
                    res.append(_mapping[i])
                rehashed = True
    return res

def names():
    return _mapping.keys()
