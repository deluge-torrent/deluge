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
# 	Boston, MA    02110-1301, USA.
#
from deluge.ui.client import client
from deluge.ui.console.main import match_torrents
import re
import logging
from twisted.internet import defer

_idregex = re.compile(r'^[0-9a-f]{40}$')

_mapping = {}

def _arg_is_id(arg):
    return bool(_idregex.match(arg))

def get_names(torrents):
    d = defer.Deferred()
    def _got_torrents_status(states):
        try:
            d.callback(list([ (tid, state['name']) for (tid, state) in states.items() ]))
        except Exception, e:
            print e
            d.errback(e)

    client.core.get_torrents_status({'id':torrents}, ['name']).addCallback(_got_torrents_status)
    return d

def rehash():
    global _mapping
    d = defer.Deferred()
    def on_match_torrents(torrents):
        def on_get_names(names):
            _mapping = dict([(x[1],x[0]) for x in names])
            d.callback()
        get_names(torrents).addCallback(on_get_names)
    match_torrents().addCallback(on_match_torrents)
    return d

def to_ids(args):
    d = defer.Deferred()
    def on_rehash(result):
        res = []
        for i in args:
            if _arg_is_id(i):
                res.append(i)
            else:
                if i in _mapping:
                    res.append(_mapping[i])
        d.callback(res)
    rehash().addCallback(on_rehash)

    return d

def names():
    return _mapping.keys()
