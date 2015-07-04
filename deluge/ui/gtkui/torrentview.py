# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""The torrent view component that lists all torrents in the session."""

import logging
import warnings

from twisted.internet import reactor

import deluge.component as component
import gi
from deluge.ui.client import client
from deluge.ui.gtkui import torrentview_data_funcs as funcs
from deluge.ui.gtkui.listview import ListView
from deluge.ui.gtkui.removetorrentdialog import RemoveTorrentDialog
from gi.repository import Gdk, GObject, Gtk

warnings.filterwarnings('error', category=UnicodeWarning)
# warnings.filterwarnings('error', message='*equal comparison failed*')

gi.require_version('Gtk', '3.0')

log = logging.getLogger(__name__)


def queue_peer_seed_sort_function(v1, v2):
    if v1 == v2:
        return 0
    if v2 < 0:
        return -1
    if v1 < 0:
        return 1
    if v1 > v2:
        return 1
    if v2 > v1:
        return -1


def queue_column_sort(model, iter1, iter2, data):
    v1 = model[iter1][data]
    v2 = model[iter2][data]
    return queue_peer_seed_sort_function(v1, v2)


def eta_column_sort(model, iter1, iter2, data):
    v1 = model[iter1][data]
    v2 = model[iter2][data]
    if v1 == v2:
        return 0
    if v1 == 0:
        return 1
    if v2 == 0:
        return -1
    if v1 > v2:
        return 1
    if v2 > v1:
        return -1


def seed_peer_column_sort(model, iter1, iter2, data):
    v1 = model[iter1][data]         # num seeds/peers
    v3 = model[iter2][data]         # num seeds/peers
    if v1 == v3:
        v2 = model[iter1][data + 1]   # total seeds/peers
        v4 = model[iter2][data + 1]   # total seeds/peers
        return queue_peer_seed_sort_function(v2, v4)
    return queue_peer_seed_sort_function(v1, v3)


class SearchBox(object):
    def __init__(self, torrentview):
        self.torrentview = torrentview
        self.window = torrentview.window

        self.visible = False
        self.search_pending = self.prefiltered = None

        self.search_box = self.window.main_builder.get_object("search_box")
        self.search_torrents_entry = self.window.main_builder.get_object("search_torrents_entry")
        self.close_search_button = self.window.main_builder.get_object("close_search_button")
        self.match_search_button = self.window.main_builder.get_object("search_torrents_match")
        self.window.connect_signals(self)

    def show(self):
        self.visible = True
        self.search_box.show_all()
        self.search_torrents_entry.grab_focus()

    def hide(self):
        self.visible = False
        self.clear_search()
        self.search_box.hide()
        self.search_pending = self.prefiltered = None

    def clear_search(self):
        if self.search_pending and self.search_pending.active():
            self.search_pending.cancel()

        if self.prefiltered:
            filter_column = self.torrentview.columns["filter"].column_indices[0]
            torrent_id_column = self.torrentview.columns["torrent_id"].column_indices[0]
            for row in self.torrentview.liststore:
                torrent_id = row[torrent_id_column]

                if torrent_id in self.prefiltered:
                    # Reset to previous filter state
                    self.prefiltered.pop(self.prefiltered.index(torrent_id))
                    row[filter_column] = not row[filter_column]

        self.prefiltered = None

        self.search_torrents_entry.set_text("")
        if self.torrentview.filter and 'name' in self.torrentview.filter:
            self.torrentview.filter.pop('name', None)
            self.search_pending = reactor.callLater(0.5, self.torrentview.update)

    def set_search_filter(self):
        if self.search_pending and self.search_pending.active():
            self.search_pending.cancel()

        if self.torrentview.filter and 'name' in self.torrentview.filter:
            self.torrentview.filter.pop('name', None)

        elif self.torrentview.filter is None:
            self.torrentview.filter = {}

        search_string = self.search_torrents_entry.get_text()
        if not search_string:
            self.clear_search()
        else:
            if self.match_search_button.get_active():
                search_string += '::match'
            self.torrentview.filter['name'] = search_string
        self.prefilter_torrentview()

    def prefilter_torrentview(self):
        filter_column = self.torrentview.columns["filter"].column_indices[0]
        torrent_id_column = self.torrentview.columns["torrent_id"].column_indices[0]
        torrent_name_column = self.torrentview.columns[_("Name")].column_indices[1]

        match_case = self.match_search_button.get_active()
        if match_case:
            search_string = self.search_torrents_entry.get_text()
        else:
            search_string = self.search_torrents_entry.get_text().lower()

        if self.prefiltered is None:
            self.prefiltered = []

        for row in self.torrentview.liststore:
            torrent_id = row[torrent_id_column]

            if torrent_id in self.prefiltered:
                # Reset to previous filter state
                self.prefiltered.pop(self.prefiltered.index(torrent_id))
                row[filter_column] = not row[filter_column]

            if not row[filter_column]:
                # Row is not visible(filtered out, but not by our filter), skip it
                continue

            if match_case:
                torrent_name = row[torrent_name_column]
            else:
                torrent_name = row[torrent_name_column].lower()

            if search_string in torrent_name and not row[filter_column]:
                row[filter_column] = True
                self.prefiltered.append(torrent_id)
            elif search_string not in torrent_name and row[filter_column]:
                row[filter_column] = False
                self.prefiltered.append(torrent_id)

    def on_close_search_button_clicked(self, widget):
        self.hide()

    def on_search_filter_toggle(self, widget):
        if self.visible:
            self.hide()
        else:
            self.show()

    def on_search_torrents_match_toggled(self, widget):
        if self.search_torrents_entry.get_text():
            self.set_search_filter()
            self.search_pending = reactor.callLater(0.7, self.torrentview.update)

    def on_search_torrents_entry_icon_press(self, entry, icon, event):
        if icon != Gtk.EntryIconPosition.SECONDARY:
            return
        self.clear_search()

    def on_search_torrents_entry_changed(self, widget):
        self.set_search_filter()
        self.search_pending = reactor.callLater(0.7, self.torrentview.update)


class TorrentView(ListView, component.Component):
    """TorrentView handles the listing of torrents."""
    def __init__(self):
        component.Component.__init__(self, "TorrentView", interval=2, depend=["SessionProxy"])
        self.window = component.get("MainWindow")
        # Call the ListView constructor
        ListView.__init__(self, self.window.main_builder.get_object("torrent_view"), "torrentview.state")
        log.debug("TorrentView Init..")

        # If we have gotten the state yet
        self.got_state = False

        # This is where status updates are put
        self.status = {}

        # We keep a copy of the previous status to compare for changes
        self.prev_status = {}

        # Register the columns menu with the listview so it gets updated accordingly.
        self.register_checklist_menu(self.window.main_builder.get_object("menu_columns"))

        # Add the columns to the listview
        self.add_text_column("torrent_id", hidden=True, unique=True)
        self.add_bool_column("dirty", hidden=True)
        self.add_func_column("#", funcs.cell_data_queue, [int],
                             status_field=["queue"],
                             sort_func=queue_column_sort)
        self.add_texticon_column(_("Name"),
                                 status_field=["state", "name"],
                                 function=funcs.cell_data_statusicon,
                                 default_sort=True)
        self.add_func_column(_("Size"), funcs.cell_data_size,
                             [GObject.TYPE_UINT64],
                             status_field=["total_wanted"])
        self.add_func_column(_("Downloaded"), funcs.cell_data_size,
                             [GObject.TYPE_UINT64],
                             status_field=["all_time_download"], default=False)
        self.add_func_column(_("Uploaded"), funcs.cell_data_size,
                             [GObject.TYPE_UINT64],
                             status_field=["total_uploaded"], default=False)
        self.add_func_column(_("Remaining"), funcs.cell_data_size, [GObject.TYPE_UINT64],
                             status_field=["total_remaining"], default=False)
        self.add_progress_column(_("Progress"),
                                 status_field=["progress", "state"],
                                 col_types=[float, str],
                                 function=funcs.cell_data_progress)
        self.add_func_column(_("Seeds"), funcs.cell_data_peer, [int, int],
                             status_field=["num_seeds", "total_seeds"],
                             sort_func=seed_peer_column_sort, default=False)
        self.add_func_column(_("Peers"), funcs.cell_data_peer, [int, int],
                             status_field=["num_peers", "total_peers"],
                             sort_func=seed_peer_column_sort, default=False)
        self.add_func_column(_("Seeds:Peers"), funcs.cell_data_ratio_seeds_peers, [float],
                             status_field=["seeds_peers_ratio"], default=False)
        self.add_func_column(_("Down Speed"), funcs.cell_data_speed_down, [float],
                             status_field=["download_payload_rate"])
        self.add_func_column(_("Up Speed"), funcs.cell_data_speed_up, [float],
                             status_field=["upload_payload_rate"])
        self.add_func_column(_("Down Limit"), funcs.cell_data_speed_limit_down, [float],
                             status_field=["max_download_speed"], default=False)
        self.add_func_column(_("Up Limit"), funcs.cell_data_speed_limit_up, [float],
                             status_field=["max_upload_speed"], default=False)
        self.add_func_column(_("ETA"), funcs.cell_data_time, [int],
                             status_field=["eta"], sort_func=eta_column_sort)
        self.add_func_column(_("Ratio"), funcs.cell_data_ratio_ratio, [float],
                             status_field=["ratio"], default=False)
        self.add_func_column(_("Avail"), funcs.cell_data_ratio_avail, [float],
                             status_field=["distributed_copies"], default=False)
        self.add_func_column(_("Added"), funcs.cell_data_date, [float],
                             status_field=["time_added"], default=False)
        self.add_func_column(_("Completed"), funcs.cell_data_date, [float],
                             status_field=["completed_time"], default=False)
        self.add_func_column(_("Complete Seen"), funcs.cell_data_date_or_never, [float],
                             status_field=["last_seen_complete"], default=False)
        self.add_texticon_column(_("Tracker"), function=funcs.cell_data_trackericon,
                                 status_field=["tracker_host", "tracker_host"], default=False)
        self.add_text_column(_("Download Folder"), status_field=["download_location"], default=False)
        self.add_text_column(_("Owner"), status_field=["owner"], default=False)
        self.add_bool_column(_("Shared"), status_field=["shared"], default=False,
                             tooltip=_("Torrent is shared between other Deluge users or not."))
        self.restore_columns_order_from_state()

        # Set filter to None for now
        self.filter = None

        # Connect Signals #
        # Connect to the 'button-press-event' to know when to bring up the
        # torrent menu popup.
        self.treeview.connect("button-press-event", self.on_button_press_event)
        # Connect to the 'key-press-event' to know when the bring up the
        # torrent menu popup via keypress.
        self.treeview.connect("key-release-event", self.on_key_press_event)
        # Connect to the 'changed' event of TreeViewSelection to get selection
        # changes.
        self.treeview.get_selection().connect("changed", self.on_selection_changed)

        self.treeview.connect("drag-drop", self.on_drag_drop)
        self.treeview.connect("drag_data_received", self.on_drag_data_received)
        self.treeview.connect("key-press-event", self.on_key_press_event)
        self.treeview.connect("columns-changed", self.on_columns_changed_event)

        client.register_event_handler("TorrentStateChangedEvent", self.on_torrentstatechanged_event)
        client.register_event_handler("TorrentAddedEvent", self.on_torrentadded_event)
        client.register_event_handler("TorrentRemovedEvent", self.on_torrentremoved_event)
        client.register_event_handler("SessionPausedEvent", self.on_sessionpaused_event)
        client.register_event_handler("SessionResumedEvent", self.on_sessionresumed_event)
        client.register_event_handler("TorrentQueueChangedEvent", self.on_torrentqueuechanged_event)

        self.search_box = SearchBox(self)
        self.permanent_status_keys = ["owner"]
        self.columns_to_update = []

    def start(self):
        """Start the torrentview"""
        # We need to get the core session state to know which torrents are in
        # the session so we can add them to our list.
        # Only get the status fields required for the visible columns
        status_fields = []
        for listview_column in self.columns.values():
            if listview_column.column.get_visible():
                if not listview_column.status_field:
                    continue
                status_fields.extend(listview_column.status_field)
        component.get("SessionProxy").get_torrents_status(
            {}, status_fields).addCallback(self._on_session_state)

    def _on_session_state(self, state):
        self.add_rows(state)
        self.got_state = True
        # Update the view right away with our status
        self.status = state
        self.set_columns_to_update()
        self.update_view(load_new_list=True)
        self.select_first_row()

    def stop(self):
        """Stops the torrentview"""
        # We need to clear the liststore
        self.treeview.get_selection().unselect_all()
        self.liststore.clear()
        self.prev_status = {}
        self.filter = None
        self.search_box.hide()

    def shutdown(self):
        """Called when GtkUi is exiting"""
        if self.window.visible():
            self.save_state()

    def save_state(self):
        """
        Saves the state of the torrent view.
        """
        ListView.save_state(self, "torrentview.state")

    def remove_column(self, header):
        """Removes the column with the name 'header' from the torrentview"""
        self.save_state()
        ListView.remove_column(self, header)

    def set_filter(self, filter_dict):
        """
        Sets filters for the torrentview..

        see: core.get_torrents_status
        """
        search_filter = self.filter and self.filter.get('name', None) or None
        self.filter = dict(filter_dict)  # Copied version of filter_dict.
        if search_filter and 'name' not in filter_dict:
            self.filter['name'] = search_filter
        self.update(select_row=True)

    def set_columns_to_update(self, columns=None):
        status_keys = []
        self.columns_to_update = []

        if columns is None:
            # We need to iterate through all columns
            columns = self.columns.keys()

        # Iterate through supplied list of columns to update
        for column in columns:
            # Make sure column is visible and has 'status_field' set.
            # If not, we can ignore it.
            if self.columns[column].column.get_visible() is True \
                    and self.columns[column].hidden is False \
                    and self.columns[column].status_field is not None:
                for field in self.columns[column].status_field:
                    status_keys.append(field)
                    self.columns_to_update.append(column)

        # Remove duplicates
        self.columns_to_update = list(set(self.columns_to_update))
        status_keys = list(set(status_keys + self.permanent_status_keys))
        return status_keys

    def send_status_request(self, columns=None, select_row=False):
        # Store the 'status_fields' we need to send to core
        status_keys = self.set_columns_to_update(columns)
        # print "status_keys:", status_keys

        # If there is nothing in status_keys then we must not continue
        if status_keys is []:
            return

        # Remove duplicates from status_key list
        status_keys = list(set(status_keys))

        # Request the statuses for all these torrent_ids, this is async so we
        # will deal with the return in a signal callback.
        d = component.get("SessionProxy").get_torrents_status(
            self.filter, status_keys).addCallback(self._on_get_torrents_status)
        if select_row:
            d.addCallback(self.select_first_row)

    def select_first_row(self, ignored=None):
        """
        Set the first row in the list selected if a selection does
        not already exist
        """
        rows = self.treeview.get_selection().get_selected_rows()[1]
        # Only select row if noe rows are selected
        if not rows:
            self.treeview.get_selection().select_path((0,))

    def update(self, select_row=False):
        """
        Sends a status request to core and updates the torrent list with the result.

        :param select_row: if the first row in the list should be selected if
                           no rows are already selected.
        :type select_row: boolean

        """
        if self.got_state:
            if self.search_box.search_pending is not None and self.search_box.search_pending.active():
                # An update request is scheduled, let's wait for that one
                return
            # Send a status request
            GObject.idle_add(self.send_status_request, None, select_row)

    def update_view(self, load_new_list=False):
        """Update the torrent view model with data we've received."""
        filter_column = self.columns["filter"].column_indices[0]
        status = self.status

        if not load_new_list:
            # Freeze notications while updating
            self.treeview.freeze_child_notify()

        # Get the columns to update from one of the torrents
        if status:
            torrent_id = status.keys()[0]
            fields_to_update = []
            for column in self.columns_to_update:
                column_index = self.get_column_index(column)
                for i, status_field in enumerate(self.columns[column].status_field):
                    # Only use columns that the torrent has in the state
                    if status_field in status[torrent_id]:
                        fields_to_update.append((column_index[i], status_field))

        # print "fields_to_update:", fields_to_update

        for row in self.liststore:
            torrent_id = row[self.columns["torrent_id"].column_indices[0]]
            # We expect the torrent_id to be in status and prev_status,
            # as it will be as long as the list isn't changed by the user

            torrent_id_in_status = False
            try:
                torrent_status = status[torrent_id]
                torrent_id_in_status = True
                if torrent_status == self.prev_status[torrent_id]:
                    # The status dict is the same, so do nothing to update for this torrent
                    continue
            except KeyError:
                pass

            if not torrent_id_in_status:
                if row[filter_column] is True:
                    row[filter_column] = False
            else:
                if row[filter_column] is False:
                    row[filter_column] = True

                # Find the fields to update
                to_update = []
                for i, status_field in fields_to_update:
                    row_value = status[torrent_id][status_field]
                    try:
                        # if row[i] != row_value:
                        to_update.append(i)
                        to_update.append(row_value)
                    except UnicodeWarning:
                        # print "UnicodeWarning:", E
                        # print "row_value: (%s) '%s'" % (type(row_value), row_value)
                        # print "row[%d]: (%s): '%s'" % (i, type(row[i]), row[i])
                        pass

                        # raise
                # Update fields in the liststore
                if to_update:
                    self.liststore.set(row.iter, *to_update)

        if load_new_list:
            # Create the model filter. This sets the model for the treeview and enables sorting.
            self.create_model_filter()
        else:
            self.treeview.thaw_child_notify()

        component.get("MenuBar").update_menu()
        self.prev_status = status

    def _on_get_torrents_status(self, status, select_row=False):
        """Callback function for get_torrents_status().  'status' should be a
        dictionary of {torrent_id: {key, value}}."""
        self.status = status
        if self.search_box.prefiltered is not None:
            self.search_box.prefiltered = None

        if self.status == self.prev_status and self.prev_status:
            # We do not bother updating since the status hasn't changed
            self.prev_status = self.status
            return
        self.update_view()

    def add_rows(self, torrent_ids):
        """Accepts a list of torrent_ids to add to self.liststore"""
        torrent_id_column = self.columns["torrent_id"].column_indices[0]
        dirty_column = self.columns["dirty"].column_indices[0]
        filter_column = self.columns["filter"].column_indices[0]
        for torrent_id in torrent_ids:
            # Insert a new row to the liststore
            row = self.liststore.append()
            self.liststore.set(row, torrent_id_column, torrent_id, dirty_column, True, filter_column, True)

    def remove_row(self, torrent_id):
        """Removes a row with torrent_id"""
        for row in self.liststore:
            if row[self.columns["torrent_id"].column_indices[0]] == torrent_id:
                self.liststore.remove(row.iter)
                # Force an update of the torrentview
                self.update()
                break

    def mark_dirty(self, torrent_id=None):
        for row in self.liststore:
            if not torrent_id or row[self.columns["torrent_id"].column_indices[0]] == torrent_id:
                # log.debug("marking %s dirty", torrent_id)
                row[self.columns["dirty"].column_indices[0]] = True
                if torrent_id:
                    break

    def get_selected_torrent(self):
        """Returns a torrent_id or None.  If multiple torrents are selected,
        it will return the torrent_id of the first one."""
        selected = self.get_selected_torrents()
        if selected:
            return selected[0]
        else:
            return selected

    def get_selected_torrents(self):
        """Returns a list of selected torrents or None"""
        torrent_ids = []
        try:
            paths = self.treeview.get_selection().get_selected_rows()[1]
        except AttributeError:
            # paths is likely None .. so lets return []
            return []
        try:
            for path in paths:
                try:
                    row = self.treeview.get_model().get_iter(path)
                except Exception as ex:
                    log.debug("Unable to get iter from path: %s", ex)
                    continue

                child_row = self.treeview.get_model().convert_iter_to_child_iter(row)
                child_row = self.treeview.get_model().get_model().convert_iter_to_child_iter(child_row)
                if self.liststore.iter_is_valid(child_row):
                    try:
                        value = self.liststore.get_value(child_row, self.columns["torrent_id"].column_indices[0])
                    except Exception as ex:
                        log.debug("Unable to get value from row: %s", ex)
                    else:
                        torrent_ids.append(value)
            if len(torrent_ids) == 0:
                return []

            return torrent_ids
        except (ValueError, TypeError):
            return []

    def get_torrent_status(self, torrent_id):
        """Returns data stored in self.status, it may not be complete"""
        try:
            return self.status[torrent_id]
        except:
            return {}

    def get_visible_torrents(self):
        return self.status.keys()

    # Callbacks #
    def on_button_press_event(self, widget, event):
        """This is a callback for showing the right-click context menu."""
        log.debug("on_button_press_event")
        # print "widget:", widget
        # print "event:", type(event)
        # print "event:", dir(event)
        # We only care about right-clicks
        if event.button == 3:
            x, y = event.get_coords()
            # print "X: %d, Y: %d" % (x, y)
            path = self.treeview.get_path_at_pos(int(x), int(y))
            # print "Path:", path
            # print "Path:", dir(path)
            if not path:
                return

            row = self.model_filter.get_iter(path[0])
            # print "row:", row
            # print "row:", dir(row)
            # print "stamp:", row.stamp

            # print "VALID:", self.model_filter.iter_is_valid(row)

            # print "model:", type(self.treeview.get_model())
            # print "model:", dir(self.treeview.get_model())
            # print "string_from_iter:", self.treeview.get_model().get_string_from_iter(row)
            # print "path2:", self.treeview.get_path(row)

            # print "VAL:", self.liststore.get_value(row, 0)

            if self.get_selected_torrents():
                if self.model_filter.get_value(row, self.columns["torrent_id"].column_indices[0]) \
                        not in self.get_selected_torrents():
                    self.treeview.get_selection().unselect_all()
                    self.treeview.get_selection().select_iter(row)
            else:
                self.treeview.get_selection().select_iter(row)
            torrentmenu = component.get("MenuBar").torrentmenu
            # torrentmenu.popup(None, None, None, event.button, event.time, None)
            # def pos(menu, icon):
            #    return (Gtk.StatusIcon.position_menu(menu, icon))
            # torrentmenu.popup_for_device(None, None, pos, self, event.button, event.time)
            torrentmenu.popup(None, None, None, None, event.button, event.time)
            # torrentmenu.popup(None, None, pos, self, event.button, event.time)
            return True

    def on_selection_changed(self, treeselection):
        """This callback is know when the selection has changed."""
        log.debug("on_selection_changed")
        component.get("TorrentDetails").update()
        component.get("MenuBar").update_menu()

    def on_drag_drop(self, widget, drag_context, x, y, timestamp):
        widget.stop_emission("drag-drop")

    def on_drag_data_received(self, widget, drag_context, x, y, selection_data, info, timestamp):
        widget.stop_emission("drag_data_received")

    def on_columns_changed_event(self, treeview):
        log.debug("Treeview Columns Changed")
        self.save_state()

    def on_torrentadded_event(self, torrent_id, from_state):
        if not from_state:
            self.add_rows([torrent_id])
            self.update()

    def on_torrentremoved_event(self, torrent_id):
        self.remove_row(torrent_id)

    def on_torrentstatechanged_event(self, torrent_id, state):
        # Update the torrents state
        for row in self.liststore:
            if not torrent_id == row[self.columns["torrent_id"].column_indices[0]]:
                continue

            for name in self.columns_to_update:
                if not self.columns[name].status_field:
                    continue
                for idx, status_field in enumerate(self.columns[name].status_field):
                    # Update all columns that use the state field to current state
                    if status_field != 'state':
                        continue
                    row[self.get_column_index(name)[idx]] = state

            if self.filter.get('state', None) is not None:
                # We have a filter set, let's see if theres anything to hide
                # and remove from status
                if torrent_id in self.status and self.status[torrent_id]['state'] != state:
                    row[self.columns["filter"].column_indices[0]] = False
                    del self.status[torrent_id]

        self.mark_dirty(torrent_id)

    def on_sessionpaused_event(self):
        self.mark_dirty()
        self.update()

    def on_sessionresumed_event(self):
        self.mark_dirty()
        self.update()

    def on_torrentqueuechanged_event(self):
        self.mark_dirty()
        self.update()

    # Handle keyboard shortcuts
    def on_key_press_event(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname is not None:
            func = getattr(self, 'keypress_' + keyname.lower(), None)
            if func:
                return func(event)

    def keypress_delete(self, event):
        log.debug("keypress_delete")
        torrents = self.get_selected_torrents()
        if torrents:
            if event.get_state() & Gdk.ModifierType.SHIFT_MASK:
                RemoveTorrentDialog(torrents, delete_files=True).run()
            else:
                RemoveTorrentDialog(torrents).run()

    def keypress_menu(self, event):
        log.debug("keypress_menu")
        if not self.get_selected_torrent():
            return

        torrentmenu = component.get("MenuBar").torrentmenu
        torrentmenu.popup(None, None, None, 3, event.time)
        return True
