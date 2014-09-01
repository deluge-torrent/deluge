#
# queuedtorrents.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
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

import base64
import os.path

import gtk, gtk.glade
import gobject
import pkg_resources

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.gtkui.ipcinterface import process_args
import deluge.common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log
import common

class QueuedTorrents(component.Component):
    def __init__(self):
        component.Component.__init__(self, "QueuedTorrents", depend=["StatusBar", "AddTorrentDialog"])
        self.queue = []
        self.status_item = None

        self.config = ConfigManager("gtkui.conf")
        self.glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui",
                                            "glade/queuedtorrents.glade"))
        self.glade.get_widget("chk_autoadd").set_active(
            self.config["autoadd_queued"])
        self.dialog = self.glade.get_widget("queued_torrents_dialog")
        self.dialog.set_icon(common.get_logo(32))

        self.glade.signal_autoconnect({
            "on_button_remove_clicked": self.on_button_remove_clicked,
            "on_button_clear_clicked": self.on_button_clear_clicked,
            "on_button_close_clicked": self.on_button_close_clicked,
            "on_button_add_clicked": self.on_button_add_clicked,
            "on_chk_autoadd_toggled": self.on_chk_autoadd_toggled
        })

        self.treeview = self.glade.get_widget("treeview")
        self.treeview.append_column(
            gtk.TreeViewColumn(_("Torrent"), gtk.CellRendererText(), text=0))

        self.liststore = gtk.ListStore(str, str)
        self.treeview.set_model(self.liststore)

    def run(self):
        self.dialog.set_transient_for(component.get("MainWindow").window)
        self.dialog.show()

    def start(self):
        if len(self.queue) == 0:
            return

        # Make sure status bar info is showing
        self.update_status_bar()

        # We only want the add button sensitive if we're connected to a host
        self.glade.get_widget("button_add").set_sensitive(True)

        if self.config["autoadd_queued"] or self.config["classic_mode"]:
            self.on_button_add_clicked(None)
        else:
            self.run()

    def stop(self):
        # We only want the add button sensitive if we're connected to a host
        self.glade.get_widget("button_add").set_sensitive(False)
        self.update_status_bar()

    def add_to_queue(self, torrents):
        """Adds the list of torrents to the queue"""
        # Add to the queue while removing duplicates
        self.queue = list(set(self.queue + torrents))

        # Update the liststore
        self.liststore.clear()
        for torrent in self.queue:
            self.liststore.append([os.path.split(torrent)[1], torrent])

        # Update the status bar
        self.update_status_bar()

    def update_status_bar(self):
        """Attempts to update status bar"""
        # If there are no queued torrents.. remove statusbar widgets and return
        if len(self.queue) == 0:
            if self.status_item != None:
                component.get("StatusBar").remove_item(self.status_item)
                self.status_item = None
            return False

        try:
            statusbar = component.get("StatusBar")
        except Exception, e:
            # The statusbar hasn't been loaded yet, so we'll add a timer to
            # update it later.
            gobject.timeout_add(100, self.update_status_bar)
            return False

        # Set the label text for statusbar
        if len(self.queue) > 1:
            label = str(len(self.queue)) + _(" Torrents Queued")
        else:
            label = str(len(self.queue)) + _(" Torrent Queued")

        # Add the statusbar items if needed, or just modify the label if they
        # have already been added.
        if self.status_item == None:
            self.status_item = component.get("StatusBar").add_item(
                stock=gtk.STOCK_SORT_DESCENDING,
                text=label,
                callback=self.on_statusbar_click)
        else:
            self.status_item.set_text(label)

        # We return False so the timer stops
        return False

    def on_statusbar_click(self, widget, event):
        log.debug("on_statusbar_click")
        self.run()

    def on_button_remove_clicked(self, widget):
        selected = self.treeview.get_selection().get_selected()[1]
        if selected != None:
            path = self.liststore.get_value(selected, 1)
            self.liststore.remove(selected)
            self.queue.remove(path)
            self.update_status_bar()

    def on_button_clear_clicked(self, widget):
        self.liststore.clear()
        del self.queue[:]
        self.update_status_bar()

    def on_button_close_clicked(self, widget):
        self.dialog.hide()

    def on_button_add_clicked(self, widget):
        # Add all the torrents in the liststore
        def add_torrent(model, path, iter, data):
            torrent_path = model.get_value(iter, 1)
            process_args([torrent_path])

        self.liststore.foreach(add_torrent, None)
        del self.queue[:]
        self.dialog.hide()
        self.update_status_bar()

    def on_chk_autoadd_toggled(self, widget):
        self.config["autoadd_queued"] = widget.get_active()
