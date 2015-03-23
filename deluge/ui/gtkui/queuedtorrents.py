# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
import os.path

from gi.repository import GObject, Gtk

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.ui.gtkui.common import get_logo
from deluge.ui.gtkui.ipcinterface import process_args

log = logging.getLogger(__name__)


class QueuedTorrents(component.Component):
    def __init__(self):
        component.Component.__init__(self, "QueuedTorrents", depend=["StatusBar", "AddTorrentDialog"])
        self.queue = []
        self.status_item = None

        self.config = ConfigManager("gtkui.conf")
        self.builder = Gtk.Builder()
        self.builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "queuedtorrents.ui"))
        )
        self.builder.get_object("chk_autoadd").set_active(self.config["autoadd_queued"])
        self.dialog = self.builder.get_object("queued_torrents_dialog")
        self.dialog.set_icon(get_logo(32))

        self.builder.connect_signals({
            "on_button_remove_clicked": self.on_button_remove_clicked,
            "on_button_clear_clicked": self.on_button_clear_clicked,
            "on_button_close_clicked": self.on_button_close_clicked,
            "on_button_add_clicked": self.on_button_add_clicked,
            "on_chk_autoadd_toggled": self.on_chk_autoadd_toggled
        })

        self.treeview = self.builder.get_object("treeview")
        self.treeview.append_column(
            Gtk.TreeViewColumn(_("Torrent"), Gtk.CellRendererText(), text=0))

        self.liststore = Gtk.ListStore(str, str)
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
        self.builder.get_object("button_add").set_sensitive(True)

        if self.config["autoadd_queued"] or self.config["classic_mode"]:
            self.on_button_add_clicked(None)
        else:
            self.run()

    def stop(self):
        # We only want the add button sensitive if we're connected to a host
        self.builder.get_object("button_add").set_sensitive(False)
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
            if self.status_item is not None:
                component.get("StatusBar").remove_item(self.status_item)
                self.status_item = None
            return False

        try:
            component.get("StatusBar")
        except Exception:
            # The statusbar hasn't been loaded yet, so we'll add a timer to
            # update it later.
            GObject.timeout_add(100, self.update_status_bar)
            return False

        # Set the label text for statusbar
        if len(self.queue) > 1:
            label = str(len(self.queue)) + _(" Torrents Queued")
        else:
            label = str(len(self.queue)) + _(" Torrent Queued")

        # Add the statusbar items if needed, or just modify the label if they
        # have already been added.
        if self.status_item is None:
            self.status_item = component.get("StatusBar").add_item(
                stock=Gtk.STOCK_SORT_DESCENDING,
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
        if selected is not None:
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
            torrent_path = model.get_value(iter, 1).decode('utf-8')
            process_args([torrent_path])

        self.liststore.foreach(add_torrent, None)
        del self.queue[:]
        self.dialog.hide()
        self.update_status_bar()

    def on_chk_autoadd_toggled(self, widget):
        self.config["autoadd_queued"] = widget.get_active()
