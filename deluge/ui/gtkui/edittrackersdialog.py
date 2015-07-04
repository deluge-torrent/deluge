# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
import os.path

from twisted.internet import defer

import deluge.component as component
from deluge.common import is_url, resource_filename
from deluge.ui.client import client
from deluge.ui.gtkui.common import get_deluge_icon
from gi.repository import Gtk

log = logging.getLogger(__name__)


class EditTrackersDialog:
    def __init__(self, torrent_id, parent=None):
        self.torrent_id = torrent_id
        self.builder = Gtk.Builder()
        # Main dialog
        self.builder.add_from_file(resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "edit_trackers.ui")
        ))
        # add tracker dialog
        self.builder.add_from_file(resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "edit_trackers.add.ui")
        ))
        # edit tracker dialog
        self.builder.add_from_file(resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "edit_trackers.edit.ui")
        ))

        self.dialog = self.builder.get_object("edit_trackers_dialog")
        self.treeview = self.builder.get_object("tracker_treeview")
        self.add_tracker_dialog = self.builder.get_object("add_tracker_dialog")
        self.add_tracker_dialog.set_transient_for(self.dialog)
        self.edit_tracker_entry = self.builder.get_object("edit_tracker_entry")
        self.edit_tracker_entry.set_transient_for(self.dialog)
        self.dialog.set_icon(get_deluge_icon())

        if parent is not None:
            self.dialog.set_transient_for(parent)

        # Connect the signals
        self.builder.connect_signals({
            "on_button_up_clicked": self.on_button_up_clicked,
            "on_button_add_clicked": self.on_button_add_clicked,
            "on_button_edit_clicked": self.on_button_edit_clicked,
            "on_button_edit_cancel_clicked": self.on_button_edit_cancel_clicked,
            "on_button_edit_ok_clicked": self.on_button_edit_ok_clicked,
            "on_button_remove_clicked": self.on_button_remove_clicked,
            "on_button_down_clicked": self.on_button_down_clicked,
            "on_button_add_ok_clicked": self.on_button_add_ok_clicked,
            "on_button_add_cancel_clicked": self.on_button_add_cancel_clicked
        })

        # Create a liststore for tier, url
        self.liststore = Gtk.ListStore(int, str)

        # Create the columns
        self.treeview.append_column(
            Gtk.TreeViewColumn(_("Tier"), Gtk.CellRendererText(), text=0))
        self.treeview.append_column(
            Gtk.TreeViewColumn(_("Tracker"), Gtk.CellRendererText(), text=1))

        self.treeview.set_model(self.liststore)
        self.liststore.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        self.dialog.connect("delete-event", self._on_delete_event)
        self.dialog.connect("response", self._on_response)

    def run(self):
        # Make sure we have a torrent_id.. if not just return
        if self.torrent_id is None:
            return

        # Get the trackers for this torrent
        session = component.get("SessionProxy")
        session.get_torrent_status(
            self.torrent_id, ["trackers"]
        ).addCallback(self._on_get_torrent_status)
        client.force_call()

        self.deferred = defer.Deferred()
        return self.deferred

    def _on_delete_event(self, widget, event):
        self.deferred.callback(Gtk.ResponseType.DELETE_EVENT)
        self.dialog.destroy()

    def _on_response(self, widget, response):
        if response == 1:
            self.trackers = []

            def each(model, path, iter, data):
                tracker = {}
                tracker["tier"] = model.get_value(iter, 0)
                tracker["url"] = model.get_value(iter, 1)
                self.trackers.append(tracker)
            self.liststore.foreach(each, None)
            if self.old_trackers != self.trackers:
                # Set the torrens trackers
                client.core.set_torrent_trackers(self.torrent_id, self.trackers)
                self.deferred.callback(Gtk.ResponseType.OK)
            else:
                self.deferred.callback(Gtk.ResponseType.CANCEL)
        else:
            self.deferred.callback(Gtk.ResponseType.CANCEL)
        self.dialog.destroy()

    def _on_get_torrent_status(self, status):
        """Display trackers dialog"""
        self.old_trackers = list(status["trackers"])
        for tracker in self.old_trackers:
            self.add_tracker(tracker["tier"], tracker["url"])
        self.dialog.show()

    def add_tracker(self, tier, url):
        """Adds a tracker to the list"""
        self.liststore.append([tier, url])

    def get_selected(self):
        """Returns the selected tracker"""
        return self.treeview.get_selection().get_selected()[1]

    def on_button_add_clicked(self, widget):
        log.debug("on_button_add_clicked")
        # Show the add tracker dialog
        self.add_tracker_dialog.show()
        self.builder.get_object("textview_trackers").grab_focus()

    def on_button_remove_clicked(self, widget):
        log.debug("on_button_remove_clicked")
        selected = self.get_selected()
        if selected is not None:
            self.liststore.remove(selected)

    def on_button_edit_clicked(self, widget):
        """edits an existing tracker"""
        log.debug("on_button_edit_clicked")
        selected = self.get_selected()
        if selected:
            tracker = self.liststore.get_value(selected, 1)
            self.builder.get_object("entry_edit_tracker").set_text(tracker)
            self.edit_tracker_entry.show()
            self.builder.get_object("edit_tracker_entry").grab_focus()

    def on_button_edit_cancel_clicked(self, widget):
        log.debug("on_button_edit_cancel_clicked")
        self.edit_tracker_entry.hide()

    def on_button_edit_ok_clicked(self, widget):
        log.debug("on_button_edit_ok_clicked")
        selected = self.get_selected()
        tracker = self.builder.get_object("entry_edit_tracker").get_text()
        self.liststore.set_value(selected, 1, tracker)
        self.edit_tracker_entry.hide()

    def on_button_up_clicked(self, widget):
        log.debug("on_button_up_clicked")
        selected = self.get_selected()
        num_rows = self.liststore.iter_n_children(None)
        if selected is not None and num_rows > 1:
            tier = self.liststore.get_value(selected, 0)
            if not tier > 0:
                return
            new_tier = tier - 1
            # Now change the tier for this tracker
            self.liststore.set_value(selected, 0, new_tier)

    def on_button_down_clicked(self, widget):
        log.debug("on_button_down_clicked")
        selected = self.get_selected()
        num_rows = self.liststore.iter_n_children(None)
        if selected is not None and num_rows > 1:
            tier = self.liststore.get_value(selected, 0)
            new_tier = tier + 1
            # Now change the tier for this tracker
            self.liststore.set_value(selected, 0, new_tier)

    def on_button_add_ok_clicked(self, widget):
        log.debug("on_button_add_ok_clicked")

        # Create a list of trackers from the textview widget
        textview = self.builder.get_object("textview_trackers")
        trackers = []
        b = textview.get_buffer()
        lines = b.get_text(b.get_start_iter(), b.get_end_iter(), True).strip().split("\n")
        for l in lines:
            if is_url(l):
                trackers.append(l)

        for tracker in trackers:
            # Figure out what tier number to use.. it's going to be the highest+1
            # Also check for duplicates
            # Check if there are any entries
            duplicate = False
            highest_tier = -1
            for row in self.liststore:
                tier = row[0]
                if tier > highest_tier:
                    highest_tier = tier
                if tracker == row[1]:
                    duplicate = True
                    break

            # If not a duplicate, then add it to the list
            if not duplicate:
                # Add the tracker to the list
                self.add_tracker(highest_tier + 1, tracker)

        # Clear the entry widget and hide the dialog
        textview.get_buffer().set_text("")
        self.add_tracker_dialog.hide()

    def on_button_add_cancel_clicked(self, widget):
        log.debug("on_button_add_cancel_clicked")
        # Clear the entry widget and hide the dialog
        b = Gtk.TextBuffer()
        self.builder.get_object("textview_trackers").set_buffer(b)
        self.add_tracker_dialog.hide()
