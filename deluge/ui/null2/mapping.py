#!/usr/bin/env python
from deluge.ui.client import aclient as client
from deluge.ui.null2.main import match_torrents
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

    client.get_torrents_status(_got_torrents_status, torrents, ['name'])
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
