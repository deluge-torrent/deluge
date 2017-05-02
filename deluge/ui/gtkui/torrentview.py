#
# torrentview.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
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
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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


"""The torrent view component that lists all torrents in the session."""

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import gettext
import gobject
import warnings
from locale import strcoll
from urlparse import urlparse

import deluge.common
import deluge.component as component
from deluge.ui.client import client
from deluge.log import LOG as log
import listview
from deluge.ui.tracker_icons import TrackerIcons
from removetorrentdialog import RemoveTorrentDialog

# Status icons.. Create them from file only once to avoid constantly
# re-creating them.
icon_downloading = gtk.gdk.pixbuf_new_from_file(
    deluge.common.get_pixmap("downloading16.png"))
icon_seeding = gtk.gdk.pixbuf_new_from_file(
    deluge.common.get_pixmap("seeding16.png"))
icon_inactive = gtk.gdk.pixbuf_new_from_file(
    deluge.common.get_pixmap("inactive16.png"))
icon_alert = gtk.gdk.pixbuf_new_from_file(
    deluge.common.get_pixmap("alert16.png"))
icon_queued = gtk.gdk.pixbuf_new_from_file(
    deluge.common.get_pixmap("queued16.png"))
icon_checking = gtk.gdk.pixbuf_new_from_file(
    deluge.common.get_pixmap("checking16.png"))

# Holds the info for which status icon to display based on state
ICON_STATE = {
    "Allocating": icon_checking,
    "Checking": icon_checking,
    "Downloading": icon_downloading,
    "Seeding": icon_seeding,
    "Paused": icon_inactive,
    "Error": icon_alert,
    "Queued": icon_queued,
    "Checking Resume Data": icon_checking
}

def _(message): return message

TRANSLATE = {
    "Downloading": _("Downloading"),
    "Seeding": _("Seeding"),
    "Paused": _("Paused"),
    "Checking": _("Checking"),
    "Queued": _("Queued"),
    "Error": _("Error"),
}

del _

def _t(text):
    if text in TRANSLATE:
        text = TRANSLATE[text]
    return _(text)

def cell_data_statusicon(column, cell, model, row, data):
    """Display text with an icon"""
    try:
        icon = ICON_STATE[model.get_value(row, data)]

        #Supress Warning: g_object_set_qdata: assertion `G_IS_OBJECT (object)' failed
        original_filters = warnings.filters[:]
        warnings.simplefilter("ignore")
        try:
            if cell.get_property("pixbuf") != icon:
                cell.set_property("pixbuf", icon)
        finally:
            warnings.filters = original_filters

    except KeyError:
        pass

def cell_data_trackericon(column, cell, model, row, data):
    def on_get_icon(icon):
        def create_blank_pixbuf():
            i = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 16, 16)
            i.fill(0x00000000)
            return i

        if icon:
            pixbuf = icon.get_cached_icon()
            if not pixbuf:
                try:
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(icon.get_filename(), 16, 16)
                except gobject.GError, e:
                    # Failed to load the pixbuf (Bad image file), so set a blank pixbuf
                    pixbuf = create_blank_pixbuf()
                finally:
                    icon.set_cached_icon(pixbuf)
        else:
            pixbuf = create_blank_pixbuf()

        #Supress Warning: g_object_set_qdata: assertion `G_IS_OBJECT (object)' failed
        original_filters = warnings.filters[:]
        warnings.simplefilter("ignore")
        try:
            if cell.get_property("pixbuf") != pixbuf:
                cell.set_property("pixbuf", pixbuf)
        finally:
            warnings.filters = original_filters

    host = model[row][data]
    if host:
        d = component.get("TrackerIcons").get(host)
        d.addCallback(on_get_icon)
    else:
        on_get_icon(None)

def cell_data_progress(column, cell, model, row, data):
    """Display progress bar with text"""
    (value, state_str) = model.get(row, *data)
    if cell.get_property("value") != value:
        cell.set_property("value", value)

    textstr = _t(state_str)
    if state_str not in ("Error", "Seeding") and value < 100:
        textstr = "%s %.2f%%" % (textstr, value)
    if cell.get_property("text") != textstr:
        cell.set_property("text", textstr)

def cell_data_queue(column, cell, model, row, data):
    value = model.get_value(row, data)
    if value < 0:
        cell.set_property("text", "")
    else:
        cell.set_property("text", str(value + 1))

def str_nocase_sort(model, iter1, iter2, data):
    """
    Sort string column data with locale.strcoll which (allegedly)
    uses ISO 14651.

    """
    try:
        v1 = model[iter1][data].lower()
        v2 = model[iter2][data].lower()
    except AttributeError:
        # Catch None type for value.
        v1 = model[iter1][data]
        v2 = model[iter2][data]
    return strcoll(v1, v2)

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
        v2 = model[iter1][data+1]   # total seeds/peers
        v4 = model[iter2][data+1]   # total seeds/peers
        return queue_peer_seed_sort_function(v2, v4)
    return queue_peer_seed_sort_function(v1, v3)

def progress_sort(model, iter1, iter2, sort_column_id):
    progress1 = model[iter1][sort_column_id]
    progress2 = model[iter2][sort_column_id]
    # Progress value is equal, so sort on state
    if progress1 == progress2:
        state1 = model[iter1][sort_column_id + 1]
        state2 = model[iter2][sort_column_id + 1]
        return cmp(state1, state2)
    return cmp(progress1, progress2)


class TorrentView(listview.ListView, component.Component):
    """TorrentView handles the listing of torrents."""
    def __init__(self):
        component.Component.__init__(self, "TorrentView", interval=2, depend=["SessionProxy"])
        self.window = component.get("MainWindow")
        # Call the ListView constructor
        listview.ListView.__init__(self,
                            self.window.main_glade.get_widget("torrent_view"),
                            "torrentview.state")
        log.debug("TorrentView Init..")

        # If we have gotten the state yet
        self.got_state = False

        # This is where status updates are put
        self.status = {}

        # We keep a copy of the previous status to compare for changes
        self.prev_status = {}

        # Register the columns menu with the listview so it gets updated
        # accordingly.
        self.register_checklist_menu(
                            self.window.main_glade.get_widget("menu_columns"))

        # Add the columns to the listview
        self.add_text_column("torrent_id", hidden=True)
        self.add_bool_column("dirty", hidden=True)
        self.add_func_column("#", cell_data_queue, [int],
                             status_field=["queue"],
                             sort_func=queue_column_sort)
        self.add_texticon_column(_("Name"),
                                 status_field=["state", "name"],
                                 function=cell_data_statusicon,
                                 sort_func=str_nocase_sort)
        self.add_func_column(_("Size"), listview.cell_data_size,
                             [gobject.TYPE_UINT64],
                             status_field=["total_wanted"])
        self.add_func_column(_("Downloaded"), listview.cell_data_size,
                             [gobject.TYPE_UINT64],
                             status_field=["all_time_download"], default=False)
        self.add_func_column(_("Uploaded"), listview.cell_data_size,
                             [gobject.TYPE_UINT64],
                             status_field=["total_uploaded"], default=False)
        self.add_progress_column(_("Progress"),
                                 status_field=["progress", "state"],
                                 col_types=[float, str],
                                 function=cell_data_progress,
                                 sort_func=progress_sort)
        self.add_func_column(_("Seeders"), listview.cell_data_peer, [int, int],
                             status_field=["num_seeds", "total_seeds"],
                             sort_func=seed_peer_column_sort, default=False)
        self.add_func_column(_("Peers"), listview.cell_data_peer, [int, int],
                             status_field=["num_peers", "total_peers"],
                             sort_func=seed_peer_column_sort, default=False)
        self.add_func_column(_("Seeders") + "/" + _("Peers"), listview.cell_data_ratio, [float],
                             status_field=["seeds_peers_ratio"], default=False)
        self.add_func_column(_("Down Speed"), listview.cell_data_speed, [int],
                             status_field=["download_payload_rate"])
        self.add_func_column(_("Up Speed"), listview.cell_data_speed, [int],
                             status_field=["upload_payload_rate"])
        self.add_func_column(_("Down Limit"), listview.cell_data_speed_limit, [float],
                             status_field=["max_download_speed"], default=False)
        self.add_func_column(_("Up Limit"), listview.cell_data_speed_limit, [float],
                             status_field=["max_upload_speed"], default=False)
        self.add_func_column(_("ETA"), listview.cell_data_time, [int],
                             status_field=["eta"], sort_func=eta_column_sort)
        self.add_func_column(_("Ratio"), listview.cell_data_ratio, [float],
                             status_field=["ratio"], default=False)
        self.add_func_column(_("Avail"), listview.cell_data_ratio, [float],
                             status_field=["distributed_copies"], default=False)
        self.add_func_column(_("Added"), listview.cell_data_date, [int],
                             status_field=["time_added"], default=False)
        self.add_texticon_column(_("Tracker"),
                                 status_field=["tracker_host", "tracker_host"],
                                 function=cell_data_trackericon, default=False)

        self.add_text_column(_("Save Path"), status_field=["save_path"], default=False)
        self.restore_columns_order_from_state()

        # Set filter to None for now
        self.filter = None

        ### Connect Signals ###
        # Connect to the 'button-press-event' to know when to bring up the
        # torrent menu popup.
        self.treeview.connect("button-press-event",
                                    self.on_button_press_event)
        # Connect to the 'key-press-event' to know when the bring up the
        # torrent menu popup via keypress.
        self.treeview.connect("key-release-event", self.on_key_press_event)
        # Connect to the 'changed' event of TreeViewSelection to get selection
        # changes.
        self.treeview.get_selection().connect("changed",
                                    self.on_selection_changed)

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

    def start(self):
        """Start the torrentview"""
        # We need to get the core session state to know which torrents are in
        # the session so we can add them to our list.
        component.get("SessionProxy").get_torrents_status({}, []).addCallback(self._on_session_state)

    def _on_session_state(self, state):
        self.add_rows(state)
        self.got_state = True
        # Update the view right away with our status
        self.status = state
        self.set_columns_to_update()
        self.update_view(load_new_list=True)

    def stop(self):
        """Stops the torrentview"""
        # Save column state before clearing liststore
        # so column sort details are correctly saved.
        self.save_state()
        self.liststore.clear()
        self.prev_status = {}

    def shutdown(self):
        """Called when GtkUi is exiting"""
        pass

    def save_state(self):
        """
        Saves the state of the torrent view.
        """
        if self.window.visible():
            listview.ListView.save_state(self, "torrentview.state")

    def remove_column(self, header):
        """Removes the column with the name 'header' from the torrentview"""
        self.save_state()
        listview.ListView.remove_column(self, header)

    def set_filter(self, filter_dict):
        """Sets filters for the torrentview..
        see: core.get_torrents_status
        """
        self.filter = dict(filter_dict) #copied version of filter_dict.
        self.update()

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

        # Remove duplicate keys
        self.columns_to_update = list(set(self.columns_to_update))
        return status_keys

    def send_status_request(self, columns=None):
        # Store the 'status_fields' we need to send to core
        status_keys = self.set_columns_to_update(columns)

        # If there is nothing in status_keys then we must not continue
        if status_keys is []:
            return

        # Remove duplicates from status_key list
        status_keys = list(set(status_keys))

        # Request the statuses for all these torrent_ids, this is async so we
        # will deal with the return in a signal callback.
        component.get("SessionProxy").get_torrents_status(
            self.filter, status_keys).addCallback(self._on_get_torrents_status)

    def update(self):
        if self.got_state:
            # Send a status request
            gobject.idle_add(self.send_status_request)

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
            except KeyError, e:
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
                    if row[i] != row_value:
                        to_update.append(i)
                        to_update.append(row_value)
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

    def _on_get_torrents_status(self, status):
        """Callback function for get_torrents_status().  'status' should be a
        dictionary of {torrent_id: {key, value}}."""
        self.status = status
        if self.status == self.prev_status and self.prev_status:
            # We do not bother updating since the status hasn't changed
            self.prev_status = self.status
            return
        gobject.idle_add(self.update_view)

    def add_row(self, torrent_id, update=True):
        """Adds a new torrent row to the treeview"""
        # Make sure this torrent isn't already in the list
        for row in self.liststore:
            if row[self.columns["torrent_id"].column_indices[0]] == torrent_id:
                # Row already in the list
                return
        # Insert a new row to the liststore
        row = self.liststore.append()
        # Store the torrent id
        self.liststore.set_value(
                    row,
                    self.columns["torrent_id"].column_indices[0],
                    torrent_id)
        if update:
            self.update()

    def add_rows(self, state):
        """Adds all the torrents from state to self.liststore"""
        torrent_id_column = self.columns["torrent_id"].column_indices[0]
        dirty_column = self.columns["dirty"].column_indices[0]
        filter_column = self.columns["filter"].column_indices[0]
        for i, torrent_id in enumerate(state):
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

    def mark_dirty(self, torrent_id = None):
        for row in self.liststore:
            if not torrent_id or row[self.columns["torrent_id"].column_indices[0]] == torrent_id:
                #log.debug("marking %s dirty", torrent_id)
                row[self.columns["dirty"].column_indices[0]] = True
                if torrent_id: break

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
                except Exception, e:
                    log.debug("Unable to get iter from path: %s", e)
                    continue

                child_row = self.treeview.get_model().convert_iter_to_child_iter(None, row)
                child_row = self.treeview.get_model().get_model().convert_iter_to_child_iter(child_row)
                if self.liststore.iter_is_valid(child_row):
                    try:
                        value = self.liststore.get_value(child_row, self.columns["torrent_id"].column_indices[0])
                    except Exception, e:
                        log.debug("Unable to get value from row: %s", e)
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

    ### Callbacks ###
    def on_button_press_event(self, widget, event):
        """This is a callback for showing the right-click context menu."""
        log.debug("on_button_press_event")
        # We only care about right-clicks
        if event.button == 3:
            x, y = event.get_coords()
            path = self.treeview.get_path_at_pos(int(x), int(y))
            if not path:
                return
            row = self.model_filter.get_iter(path[0])

            if self.get_selected_torrents():
                if self.model_filter.get_value(row, self.columns["torrent_id"].column_indices[0]) not in self.get_selected_torrents():
                    self.treeview.get_selection().unselect_all()
                    self.treeview.get_selection().select_iter(row)
            else:
                self.treeview.get_selection().select_iter(row)
            torrentmenu = component.get("MenuBar").torrentmenu
            torrentmenu.popup(None, None, None, event.button, event.time)
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

    def on_torrentadded_event(self, torrent_id):
        if self.got_state is False:
            return
        self.add_row(torrent_id)
        self.mark_dirty(torrent_id)

    def on_torrentremoved_event(self, torrent_id):
        self.remove_row(torrent_id)

    def on_torrentstatechanged_event(self, torrent_id, state):
        # Update the torrents state
        for row in self.liststore:
            if not torrent_id == row[self.columns["torrent_id"].column_indices[0]]:
                continue
            row[self.get_column_index(_("Progress"))[1]] = state

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
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname is not None:
            func = getattr(self, 'keypress_' + keyname, None)
            if func:
                return func(event)

    def keypress_Delete(self, event):
        log.debug("keypress_Delete")
        torrents = self.get_selected_torrents()
        if torrents:
            RemoveTorrentDialog(torrents).run()

    def keypress_Menu(self, event):
        log.debug("keypress_Menu")
        if not self.get_selected_torrent():
            return

        torrentmenu = component.get("MenuBar").torrentmenu
        torrentmenu.popup(None, None, None, 3, event.time)
        return True
