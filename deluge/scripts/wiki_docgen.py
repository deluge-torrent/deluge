#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
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

#
#generate docs for deluge-wiki
#client doc's For core.
#

from deluge.core.core import Core
from deluge.ui.client import aclient, sclient
import pydoc
import inspect
import textwrap
sclient.set_core_uri()
print "\n\n"


if 0: #aclient non-core
    methods = sorted([m for m  in dir(aclient) if not m.startswith('_')
        if not m in ['add_torrent_file', 'has_callback', 'get_method',
            'methodHelp','methodSignature','list_methods','add_torrent_file_binary']])

    for m in methods:
        func = getattr(aclient, m)
        method_name = m
        if method_name in dir(aclient):
            func = getattr(aclient, method_name)
        try:
            params = inspect.getargspec(func)[0][1:]
        except:
            continue

        print("\n'''%s(%s): '''\n" %(method_name, ", ".join(params)))
        print("%s" % pydoc.getdoc(func))

if 1: #baseclient/core
    methods = sorted([m for m in dir(Core) if m.startswith("export")]
        + ['export_add_torrent_file_binary'] #HACK

        )

    for m in methods:

        method_name = m[7:]
        if method_name in dir(aclient):
            func = getattr(aclient, method_name)
        else:
            func = getattr(Core, m)

        params = inspect.getargspec(func)[0][1:]
        if (aclient.has_callback(method_name)
                and not method_name in ['add_torrent_file_binary']):
            params = ["[callback]"] + params

        print("\n'''%s(%s): '''\n" %(method_name, ", ".join(params)))
        print("{{{\n%s\n}}}" % pydoc.getdoc(func))

if 0: #plugin-manager
    import WebUi
    from WebUi.pluginmanager import PluginManager

    for m in methods:
        func = getattr(PluginManager, m)
        method_name = m
        params = inspect.getargspec(func)[0][1:]
        print("\n'''%s(%s): '''\n" %(method_name, ", ".join(params)))
        print("%s" % pydoc.getdoc(func))

if 0: #possible config-values
    print "=== config-values ==="
    cfg = sclient.get_sconfig()
    for key in sorted(cfg.keys()):
        print "%s:%s()" % (key, type(cfg[key]).__name__)

if 0: #keys
    print """== Notes ==
* The available keys for get_torrent_status(id, keys)
    {{{
#!python
>>>sorted(sclient.get_status_keys())"""
    print "\n".join(textwrap.wrap(str(sorted(sclient.get_status_keys())),100))
    print """}}}"""




print "\n\n"
