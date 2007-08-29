# -*- coding: utf-8 -*-
#
# update.py
#
# Copyright (C) Marcos Pinto 2007 <markybob@gmail.com>
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

import urllib
import sys

import __init__

try:
    new_release = urllib.urlopen("http://download.deluge-torrent.org/version").read().strip()
except IOError:
    print "Network error while trying to check for a newer version of Deluge"
    new_release = ""

if new_release >  sys.argv[1]:
    import gtk
    import pygtk
    dialog = gtk.MessageDialog(parent = None,
                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    buttons = gtk.BUTTONS_YES_NO,
                    message_format=_("There is a newer version of Deluge.  Would you like to be taken to our download site?"),
                    type=gtk.MESSAGE_QUESTION)
    dialog.set_title('New Release!')
    import time
    #give main client time to get up and running so we dont get placed in the
    #background and hidden.  also sleep this long for blocklist import
    time.sleep(20)
    result = dialog.run()
    dialog.destroy()
    if result == gtk.RESPONSE_YES:
        import os
        os.spawnlp(os.P_NOWAIT, 'python', 'python', '-c', "import webbrowser; webbrowser.open('http://download.deluge-torrent.org/')")
    elif result == gtk.RESPONSE_NO:
        pass
