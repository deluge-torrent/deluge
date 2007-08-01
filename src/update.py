#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import sys

new_release = urllib.urlopen("http://download.deluge-torrent.org/version").read().strip()
if new_release >  sys.argv[1]:
    import gtk
    import pygtk
    dialog = gtk.MessageDialog(parent = None,
                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    buttons = gtk.BUTTONS_YES_NO,
                    message_format="There is a newer version of Deluge.  Would you like to be taken to our download site?",
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
