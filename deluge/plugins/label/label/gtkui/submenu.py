#
# submenu.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
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
# 	Boston, MA  02110-1301, USA.
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


import os
import pkg_resources    # access plugin egg
from deluge.log import LOG as log
from deluge import component    # for systray
import gtk, gobject
from deluge.ui.client import client

# Deferred Translation
def _(message): return message
NO_LABEL = _("No Label")
del _

class LabelMenu(gtk.MenuItem):
    def __init__(self):
        gtk.MenuItem.__init__(self, _("Label"))

        self.sub_menu = gtk.Menu()
        self.set_submenu(self.sub_menu)
        self.items = []

        #attach..
        torrentmenu = component.get("MenuBar").torrentmenu
        self.sub_menu.connect("show", self.on_show, None)

    def get_torrent_ids(self):
        return component.get("TorrentView").get_selected_torrents()

    def on_show(self, widget=None, data=None):
        log.debug("label-on-show")
        client.label.get_labels().addCallback(self.cb_labels)

    def cb_labels(self, labels):
        for child in self.sub_menu.get_children():
            self.sub_menu.remove(child)
        for label in [NO_LABEL] + list(labels):
            if label == NO_LABEL:
                item = gtk.MenuItem(_(NO_LABEL))
            else:
                item = gtk.MenuItem(label.replace("_","__"))
            item.connect("activate", self.on_select_label, label)
            self.sub_menu.append(item)
        self.show_all()

    def on_select_label(self, widget=None, label_id=None):
        log.debug("select label:%s,%s" % (label_id ,self.get_torrent_ids()) )
        for torrent_id in self.get_torrent_ids():
            client.label.set_torrent(torrent_id, label_id)
