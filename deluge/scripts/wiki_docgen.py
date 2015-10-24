#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

#
# generate docs for deluge-wiki
# client doc's For core.
#

from __future__ import print_function

import inspect
import pydoc
import textwrap

from deluge.core.core import Core
from deluge.ui.client import aclient, sclient

sclient.set_core_uri()
print("\n\n")


if 0:  # aclient non-core
    methods = sorted([m for m in dir(aclient) if not m.startswith('_')
                      if m not in ['add_torrent_file', 'has_callback', 'get_method', 'methodHelp',
                                   'methodSignature', 'list_methods', 'add_torrent_file_binary']])

    for m in methods:
        func = getattr(aclient, m)
        method_name = m
        if method_name in dir(aclient):
            func = getattr(aclient, method_name)
        try:
            params = inspect.getargspec(func)[0][1:]
        except Exception:
            continue

        print("\n'''%s(%s): '''\n" % (method_name, ", ".join(params)))
        print("%s" % pydoc.getdoc(func))

if 1:  # baseclient/core
    methods = sorted([m for m in dir(Core) if m.startswith("export")] +
                     ['export_add_torrent_file_binary'])  # HACK

    for m in methods:

        method_name = m[7:]
        if method_name in dir(aclient):
            func = getattr(aclient, method_name)
        else:
            func = getattr(Core, m)

        params = inspect.getargspec(func)[0][1:]
        if aclient.has_callback(method_name) and method_name not in ['add_torrent_file_binary']:
            params = ["[callback]"] + params

        print("\n'''%s(%s): '''\n" % (method_name, ", ".join(params)))
        print("{{{\n%s\n}}}" % pydoc.getdoc(func))

if 0:  # plugin-manager
    from WebUi.pluginmanager import PluginManager

    for m in methods:
        func = getattr(PluginManager, m)
        method_name = m
        params = inspect.getargspec(func)[0][1:]
        print("\n'''%s(%s): '''\n" % (method_name, ", ".join(params)))
        print("%s" % pydoc.getdoc(func))

if 0:  # possible config-values
    print("=== config-values ===")
    cfg = sclient.get_sconfig()
    for key in sorted(cfg.keys()):
        print("%s:%s()" % (key, type(cfg[key]).__name__))

if 0:  # keys
    print("""== Notes ==
* The available keys for get_torrent_status(id, keys)
    {{{
#!python
>>>sorted(sclient.get_status_keys())""")
    print("\n".join(textwrap.wrap(str(sorted(sclient.get_status_keys())), 100)))
    print("""}}}""")

print("\n\n")
