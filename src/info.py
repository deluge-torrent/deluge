#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import platform
import common
import gtk
pygtk = '%i.%i.%i' %(gtk.pygtk_version[0],gtk.pygtk_version[1],gtk.pygtk_version[2])

urllib.urlopen("http://download.deluge-torrent.org/stats.php?processor=" + \
    platform.machine() + "&python=" + platform.python_version() \
    + "&os=" + platform.system() + "&pygtk=" + pygtk)

f = open(common.CONFIG_DIR + '/infosent', 'w')
f.write("")
f.close
