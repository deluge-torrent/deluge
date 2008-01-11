#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# webserver_framework.py
#
# Copyright (C) Martijn Voncken 2007 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
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
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.
"""
json api.
only used for XUL and/or external scripts
it would be possible not to include the python-json dependency.
"""

from new import instancemethod
from inspect import getargspec
from utils import ws,get_torrent_status,get_category_choosers, get_stats,filter_torrent_state,fsize,fspeed
from page_decorators import remote
from operator import attrgetter
import lib.webpy022 as web
proxy = ws.proxy

def to_json(obj):
    from lib.pythonize import pythonize
    obj = pythonize(obj)
    try:
        import json
        return json.write(obj)
    except ImportError:
        raise ImportError("""Install python-json using your package-manager
        http://sourceforge.net/projects/json-py/""")

class json_api:
    """
    eperimental json api
    generic proxy for all methods onm self.
    """
    illegal_methods = ['shutdown', 'socket', 'xmlrpclib','pickle','os',
        'is_localhost','CoreProxy','connect_on_new_core', 'connect_on_no_core',
        'connected','deluge','GET','POST']
    def __init__(self):
        self._add_proxy_methods()

    #extra exposed:
    get_torrent_status = get_torrent_status

    @remote
    def POST(self,name):
        import json
        if name.startswith('_'):
            raise AttributeError('_ methods are illegal.')
        if name in self.illegal_methods:
            raise AttributeError('Illegal method.')
        if not(hasattr(self,name)):
            raise AttributeError('No such method')

        method = getattr(self,name)
        vars = web.input(kwargs= None)
        ws.log.debug('vars=%s' % vars)
        if vars.kwargs:
            kwargs = json.read(vars.kwargs)
        else:
            kwargs = {}

        result = method(**kwargs)

        return "(" + to_json(result) + ")"


    def list_methods(self):
        """
        list all json methods
        returns a dict of {methodname:{args:[list of kwargs],doc:'string'},..}
        """
        methods = [getattr(self,m) for m in dir(self)
            if not m.startswith('_')
            and (not m in self.illegal_methods)
            and callable(getattr(self,m))
            ]

        return dict([(f.__name__,
            {'args':getargspec(f)[0],'doc':(f.__doc__ or '').strip()})
            for f in methods])

    def _add_proxy_methods(self):
        methods = [getattr(proxy,m) for m in dir(proxy)
            if not m.startswith('_')
            and (not m in self.illegal_methods)
            and callable(getattr(proxy,m))
            ]
        for m in methods:
            setattr(self,m.__name__,m)

    #extra's:
    def list_torrents(self):
        return [get_torrent_status(torrent_id)
            for torrent_id in ws.proxy.get_session_state()]

    def simplify_torrent_status(self, torrent):
        """smaller subset and preformatted data for the treelist"""
        data = {
            "id":torrent.id,
            "message":torrent.message,
            "name":torrent.name,
            "total_size":fsize(torrent.total_size),
            "progress":torrent.progress,
            "category":torrent.category,
            "seeds":"",
            "peers":"",
            "download_rate":"",
            "upload_rate":"",
            "eta":"",
            "distributed_copies":"",
            "ratio":"",
            "calc_state_str":torrent.calc_state_str,
            "queue_pos":torrent.queue_pos
        }
        if torrent.total_seeds > 0:
            data['seeds'] = "%s (%s)" % (torrent.num_seeds, torrent.total_seeds)
        if torrent.total_peers > 0:
            data['peers'] = "%s (%s)" % (torrent.num_peers, torrent.total_peers)
        if torrent.download_rate > 0:
            data['download_rate'] =  fspeed(torrent.download_rate)
        if torrent.upload_rate > 0:
            data['upload_rate'] = fspeed(torrent.upload_rate)
        if torrent.eta > 0:
            data['eta'] = ("%.3f" % torrent.eta)
        if torrent.distributed_copies > 0:
            data['distributed_copies'] = "%.3f" % torrent.distributed_copies
        if torrent.ratio > 0:
            data['ratio'] = "%.3f" % torrent.ratio
        return data

    def update_ui(self, filter=None, category=None ,sort='name' ,order='down'):
        """
        Combines the most important ui calls into 1 composite call.
        xmlhttp requests are expensive,max 2 running at the same time.
        and performance over the internet is mostly related to the number
        of requests (low ping)
        returns :
        {torrent_list:[{},..],'categories':[],'filters':'','stats':{}}
        """
        torrent_list = self.list_torrents();
        filter_tabs, category_tabs = get_category_choosers(torrent_list)


        #filter-state
        if filter:
            torrent_list = filter_torrent_state(torrent_list, filter)

        #filter-cat
        if category:
            torrent_list = [t for t in torrent_list if t.category == category]

        #sorting
        if sort:
            torrent_list.sort(key=attrgetter(sort))
            if order == 'up':
                torrent_list = reversed(torrent_list)

        torrent_list = [self.simplify_torrent_status(t) for t in torrent_list]

        return {
            'torrent_list':torrent_list,
            'categories':category_tabs,
            'filters':filter_tabs,
            'stats':get_stats()
        }



if __name__ == '__main__':
    from pprint import pprint
    #proxy.set_core_uri('http://localhost:58846') #How to configure this?
    j = json_api()
    if True:
        print 'list-methods:'
        methods = j.list_methods()
        names = methods.keys()
        names.sort()
        for name in names:
            m = methods[name]
            print "%s(%s)\n        %s\n" % (name , m['args'] , m['doc'])

        #j.GET('list_torrents')
        j.POST('list_torrents')

