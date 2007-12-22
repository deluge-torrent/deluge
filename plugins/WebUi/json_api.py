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
it would be possible not to incluse the python-json dependency.
"""

import deluge.ui.client as proxy
from new import instancemethod
from inspect import getargspec
from webserver_framework import remote,ws,get_torrent_status,log
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

    @remote
    def GET(self,name):
        if name.startswith('_'):
            raise AttributeError('_ methods are illegal!')
        if name in self.illegal_methods:
            raise AttributeError('Illegal method , I smell a rat!')
        if not(hasattr(self,name)):
            raise AttributeError('No such Method')

        method = getattr(self,name)
        kwargs = {}

        result = method(**kwargs)

        return to_json(result)

    POST = GET

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

    get_torrent_status = get_torrent_status



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

