#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import platform
import common
import sys

py_version = sys.version[:3]

urllib.urlopen("http://download.deluge-torrent.org/stats.php?processor=" + \
    platform.machine() + "&python=" + platform.python_version() \
    + "&os=" + platform.system())

f = open(common.CONFIG_DIR + '/infosent', 'w')
print "writing file infosent"
f.write("")
f.close
