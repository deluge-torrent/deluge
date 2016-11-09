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
import time
from locale import strcoll

import gobject
import gtk
import pygtk
from twisted.internet import reactor

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.gtkui import torrentview_data_funcs as funcs
from deluge.ui.gtkui.listview import ListView
from deluge.ui.gtkui.removetorrentdialog import RemoveTorrentDialog
from deluge.ui.sessionproxy import TorrrentsState

pygtk.require('2.0')

log = logging.getLogger(__name__)


def str_nocase_sort(model, iter1, iter2, data):
    """
    Sort string column data with locale.strcoll which (allegedly) uses ISO 14651.

    """
    v1 = model[iter1][data].lower()
    v2 = model[iter2][data].lower()
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
        v2 = model[iter1][data + 1]   # total seeds/peers
        v4 = model[iter2][data + 1]   # total seeds/peers
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


class SearchBox(object):
    def __init__(self, torrentview):
        self.torrentview = torrentview
        self.window = torrentview.window

        self.visible = False
        self.search_pending = self.prefiltered = None

        self.search_box = self.window.main_builder.get_object('search_box')
        self.search_torrents_entry = self.window.main_builder.get_object('search_torrents_entry')
        self.close_search_button = self.window.main_builder.get_object('close_search_button')
        self.match_search_button = self.window.main_builder.get_object('search_torrents_match')
        self.window.connect_signals(self)

    def show(self):
        self.visible = True
        self.search_box.show_all()
        self.search_torrents_entry.grab_focus()

    def hide(self):
        self.visible = False
        self.clear_search()
        self.search_box.hide_all()
        self.search_pending = self.prefiltered = None

    def clear_search(self):
        if self.search_pending and self.search_pending.active():
            self.search_pending.cancel()

        if self.prefiltered:
            filter_column = self.torrentview.columns['filter'].column_indices[0]
            torrent_id_column = self.torrentview.columns['torrent_id'].column_indices[0]
            for row in self.torrentview.liststore:
                torrent_id = row[torrent_id_column]

                if torrent_id in self.prefiltered:
                    # Reset to previous filter state
                    self.prefiltered.pop(self.prefiltered.index(torrent_id))
                    row[filter_column] = not row[filter_column]

        self.prefiltered = None

        self.search_torrents_entry.set_text('')
        if 'search' in self.torrentview.torrents_state.filter:
            self.torrentview.torrents_state.set_filter({'search': None})
            self.search_pending = reactor.callLater(0.5, self.torrentview.update)

    def set_search_filter(self):
        if self.search_pending and self.search_pending.active():
            self.search_pending.cancel()

        search_string = self.search_torrents_entry.get_text()
        search_filter = None
        if not search_string:
            self.clear_search()
        else:
            search_filter = {'expression': search_string, 'match_case': self.match_search_button.get_active()}
        self.torrentview.set_filter({'search': search_filter})
        self.prefilter_torrentview()

    def prefilter_torrentview(self):
        filter_column = self.torrentview.columns['filter'].column_indices[0]
        torrent_id_column = self.torrentview.columns['torrent_id'].column_indices[0]
        torrent_name_column = self.torrentview.columns[_('Name')].column_indices[1]

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
        if icon != gtk.ENTRY_ICON_SECONDARY:
            return
        self.clear_search()

    def on_search_torrents_entry_changed(self, widget):
        self.set_search_filter()
        self.search_pending = reactor.callLater(0.7, self.torrentview.update)


class TorrentView(ListView, component.Component):
    """TorrentView handles the listing of torrents."""
    def __init__(self, update_interval=1):
        component.Component.__init__(self, 'TorrentView', interval=update_interval, depend=['SessionProxy'])
        self.window = component.get('MainWindow')
        # Call the ListView constructor
        ListView.__init__(self, self.window.main_builder.get_object('torrent_view'), 'torrentview.state')
        log.debug('TorrentView Init..')

        # The state of the torrents in the view
        self.torrents_state = TorrrentsState()

        # Register the columns menu with the listview so it gets updated accordingly.
        self.register_checklist_menu(self.window.main_builder.get_object('menu_columns'))

        # Add the columns to the listview
        self.add_text_column('torrent_id', hidden=True, unique=True)
        self.add_func_column('#', funcs.cell_data_queue, [int],
                             status_field=['queue'],
                             sort_func=queue_column_sort)
        self.add_texticon_column(_('Name'),
                                 status_field=['state', 'name'],
                                 function=funcs.cell_data_statusicon,
                                 default_sort=True)
        self.add_func_column(_('Size'), funcs.cell_data_size,
                             [gobject.TYPE_UINT64],
                             status_field=['total_wanted'])
        self.add_func_column(_('Downloaded'), funcs.cell_data_size,
                             [gobject.TYPE_UINT64],
                             status_field=['all_time_download'], default=False)
        self.add_func_column(_('Uploaded'), funcs.cell_data_size,
                             [gobject.TYPE_UINT64],
                             status_field=['total_uploaded'], default=False)
        self.add_func_column(_('Remaining'), funcs.cell_data_size, [gobject.TYPE_UINT64],
                             status_field=['total_remaining'], default=False)
        self.add_progress_column(_('Progress'),
                                 status_field=['progress', 'state'],
                                 col_types=[float, str],
                                 function=funcs.cell_data_progress,
                                 sort_func=progress_sort)
        self.add_func_column(_('Seeds'), funcs.cell_data_peer, [int, int],
                             status_field=['num_seeds', 'total_seeds'],
                             sort_func=seed_peer_column_sort, default=False)
        self.add_func_column(_('Peers'), funcs.cell_data_peer, [int, int],
                             status_field=['num_peers', 'total_peers'],
                             sort_func=seed_peer_column_sort, default=False)
        self.add_func_column(_('Seeds:Peers'), funcs.cell_data_ratio_seeds_peers, [float],
                             status_field=['seeds_peers_ratio'], default=False)
        self.add_func_column(_('Down Speed'), funcs.cell_data_speed_down, [int],
                             status_field=['download_payload_rate'])
        self.add_func_column(_('Up Speed'), funcs.cell_data_speed_up, [int],
                             status_field=['upload_payload_rate'])
        self.add_func_column(_('Down Limit'), funcs.cell_data_speed_limit_down, [float],
                             status_field=['max_download_speed'], default=False)
        self.add_func_column(_('Up Limit'), funcs.cell_data_speed_limit_up, [float],
                             status_field=['max_upload_speed'], default=False)
        self.add_func_column(_('ETA'), funcs.cell_data_time, [int],
                             status_field=['eta'], sort_func=eta_column_sort)
        self.add_func_column(_('Ratio'), funcs.cell_data_ratio_ratio, [float],
                             status_field=['ratio'], default=False)
        self.add_func_column(_('Avail'), funcs.cell_data_ratio_avail, [float],
                             status_field=['distributed_copies'], default=False)
        self.add_func_column(_('Added'), funcs.cell_data_date_added, [int],
                             status_field=['time_added'], default=False)
        self.add_func_column(_('Completed'), funcs.cell_data_date_completed, [int],
                             status_field=['completed_time'], default=False)
        self.add_func_column(_('Complete Seen'), funcs.cell_data_date_or_never, [int],
                             status_field=['last_seen_complete'], default=False)
        self.add_texticon_column(_('Tracker'), function=funcs.cell_data_trackericon,
                                 status_field=['tracker_host', 'tracker_host'], default=False)
        self.add_text_column(_('Download Folder'), status_field=['download_location'], default=False)
        self.add_text_column(_('Owner'), status_field=['owner'], default=False)
        self.add_bool_column(_('Shared'), status_field=['shared'], default=False,
                             tooltip=_('Torrent is shared between other Deluge users or not.'))
        self.restore_columns_order_from_state()

        # Connect Signals #
        # Connect to the 'button-press-event' to know when to bring up the
        # torrent menu popup.
        self.treeview.connect('button-press-event', self.on_button_press_event)
        # Connect to the 'key-press-event' to know when the bring up the
        # torrent menu popup via keypress.
        self.treeview.connect('key-release-event', self.on_key_press_event)
        # Connect to the 'changed' event of TreeViewSelection to get selection
        # changes.
        self.treeview.get_selection().connect('changed', self.on_selection_changed)

        self.treeview.connect('drag-drop', self.on_drag_drop)
        self.treeview.connect('drag_data_received', self.on_drag_data_received)
        self.treeview.connect('key-press-event', self.on_key_press_event)
        self.treeview.connect('columns-changed', self.on_columns_changed_event)

        self.search_box = SearchBox(self)
        self.permanent_status_keys = ['owner', 'tracker_status', 'state']
        self.columns_to_update = []
        self.last_status_update_ts = time.time()

    def start(self):
        """Start the torrentview"""
        status_keys = self.set_columns_to_update()
        component.get('SessionProxy').get_torrents_status(
            self.torrents_state, status_keys, only_updated=False, from_cache=False
        ).addCallback(self._on_session_state)

        client.register_event_handler('TorrentAddedEvent', self.on_torrentadded_event)
        client.register_event_handler('TorrentQueueChangedEvent', self.on_torrentqueuechanged_event)
        client.register_event_handler('TorrentRemovedEvent', self.on_torrentremoved_event)
        client.register_event_handler('SessionPausedEvent', self.on_sessionpaused_event)
        client.register_event_handler('SessionProxyUpdateEvent', self._on_session_proxy_update)
        client.register_event_handler('SessionResumedEvent', self.on_sessionresumed_event)

    def _on_session_proxy_update(self, torrent_id, kw):
        self.update(from_cache=True)

    def _on_session_state(self, update):
        self.torrents_state.status = update.status
        self.torrents_state.status = {}
        self.add_rows(update.status)
        # Update the view right away with our status
        self.set_columns_to_update()
        self.update_view(update.keys, load_new_list=True)
        self.select_first_row()

    def stop(self):
        """Stops the torrentview"""
        # We need to clear the liststore
        client.deregister_event_handler('TorrentAddedEvent', self.on_torrentadded_event)
        client.deregister_event_handler('TorrentQueueChangedEvent', self.on_torrentqueuechanged_event)
        client.deregister_event_handler('TorrentRemovedEvent', self.on_torrentremoved_event)
        client.deregister_event_handler('SessionPausedEvent', self.on_sessionpaused_event)
        client.deregister_event_handler('SessionProxyUpdateEvent', self._on_session_proxy_update)
        client.deregister_event_handler('SessionResumedEvent', self.on_sessionresumed_event)

        if self.treeview.get_selection():
            self.treeview.get_selection().unselect_all()
        self.liststore.clear()
        self.torrents_state.filter = {}
        self.torrents_state.status = None
        self.search_box.hide()

    def shutdown(self):
        """Called when GtkUi is exiting"""
        self.save_state()

    def save_state(self):
        """
        Saves the state of the torrent view.
        """
        if self.window.visible():
            ListView.save_state(self, 'torrentview.state')

    def remove_column(self, header):
        """Removes the column with the name 'header' from the torrentview"""
        self.save_state()
        ListView.remove_column(self, header)

    def set_filter(self, filter_dict):
        """
        Sets filters for the torrentview..

        see: core.get_torrents_status
        """
        self.torrents_state.set_filter(filter_dict)
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

        # Use set to remove duplicates
        self.columns_to_update = list(set(self.columns_to_update))
        status_keys = list(set(status_keys + self.permanent_status_keys))
        return status_keys

    def send_status_request(self, columns=None, select_row=False, from_cache=True):
        status_keys = self.set_columns_to_update(columns)
        # Request the statuses for all these torrent_ids, this is async so we
        # will deal with the return in a signal callback.
        d = component.get('SessionProxy').get_torrents_status(self.torrents_state, status_keys,
                                                              only_updated=not self.torrents_state.filter_changed,
                                                              from_cache=from_cache)
        d.addCallback(self.on_get_torrents_status)
        if select_row:
            d.addCallback(self.select_first_row)

    def on_get_torrents_status(self, state_update):
        """
        Callback function for SessionProxy.get_torrents_status()

        Args:
            state_update (StateUpdate): A sessionpoxy.StateUpdate object
                                        describing the state update.

        """
        if self.search_box.prefiltered is not None:
            self.search_box.prefiltered = None

        self.torrents_state.update_status(state_update)
        self.update_view(state_update.keys, state_update=state_update)

    def select_first_row(self, ignored=None):
        """
        Set the first row in the list selected if a selection does
        not already exist
        """
        rows = self.treeview.get_selection().get_selected_rows()[1]
        # Only select row if noe rows are selected
        if not rows:
            self.treeview.get_selection().select_path((0,))

    def update(self, select_row=False, from_cache=True):
        """
        Sends a status request to core and updates the torrent list with the result.

        :param select_row: if the first row in the list should be selected if
                           no rows are already selected.
        :type select_row: boolean

        """
        if self.torrents_state.status is None:
            return

        if self.search_box.search_pending is not None and self.search_box.search_pending.active():
            # An update request is scheduled, let's wait for that one
            return

        # Last status request was sent less than 100 ms ago, ignore
        if (time.time() - self.last_status_update_ts) < 0.1:
            return

        self.last_status_update_ts = time.time()

        # Send a status request
        gobject.idle_add(self.send_status_request, None, select_row, from_cache)

    def update_view(self, keys, load_new_list=False, state_update=None):
        """
        Update the torrent view model with data we've received.

        Args:
            keys (list): The keys to update
            load_new_list (bool): If the torrent list is loaded from scratch.
            state_update (StateUpdate): A deluge.ui.sessionproxy.StateUpdate object
        """
        filter_column = self.columns['filter'].column_indices[0]
        status = self.torrents_state.status
        updated_ids = state_update.updated_ids if state_update is not None else None
        to_show = state_update.new_matching if state_update is not None else set()
        to_hide = state_update.not_matching if state_update is not None else set()

        if not load_new_list:
            # Freeze notications while updating
            self.treeview.freeze_child_notify()

        if status:
            fields_to_update = []
            for column in self.columns_to_update:
                column_index = self.get_column_index(column)
                for i, status_field in enumerate(self.columns[column].status_field):
                    # Only use columns that the torrent has in the state
                    if status_field in keys:
                        fields_to_update.append((column_index[i], status_field))

        for i, row in enumerate(self.liststore):
            torrent_id = row[self.columns['torrent_id'].column_indices[0]]

            if updated_ids is not None:
                if torrent_id not in updated_ids and torrent_id not in to_hide and torrent_id not in to_show:
                    # Nothing to do for this torrent id, so continue
                    continue

            to_update = []
            torrent_id_in_status = False
            try:
                torrent_status = status[torrent_id]
                torrent_id_in_status = True
            except KeyError:
                pass

            if to_hide and torrent_id in to_hide:
                to_update.append(filter_column)
                to_update.append(False)
            elif to_show and torrent_id in to_show:
                to_update.append(filter_column)
                to_update.append(True)

            # Find the fields to update
            if torrent_id_in_status:
                for i, status_field in fields_to_update:
                    try:
                        row_value = torrent_status[status_field]
                        if row[i] != row_value:
                            to_update.append(i)
                            to_update.append(row_value)
                    except KeyError as ex:
                        log.warn('KeyError when getting torrent value: %s', ex)

            # Update fields in the liststore
            if to_update:
                try:
                    self.liststore.set(row.iter, *to_update)
                except Exception as ex:
                    log.warn('Error when updating liststore: %s', ex)

        if load_new_list:
            # Create the model filter. This sets the model for the treeview and enables sorting.
            self.create_model_filter()
        else:
            self.treeview.thaw_child_notify()

        component.get('MenuBar').update_menu()

    def add_rows(self, torrent_ids):
        """Accepts a list of torrent_ids to add to self.liststore"""
        torrent_id_column = self.columns['torrent_id'].column_indices[0]
        filter_column = self.columns['filter'].column_indices[0]
        # Must also set the state field used by the cell_data_progress data_func.
        progress_state_column = self.columns['Progress'].column_indices[1]

        for torrent_id in torrent_ids:
            # Insert a new row to the liststore
            row = self.liststore.append()
            # Values are set by the column index followed by the value
            self.liststore.set(row, torrent_id_column, torrent_id, filter_column, True, progress_state_column, '')

    def remove_row(self, torrent_id):
        """Removes a row with torrent_id"""
        for row in self.liststore:
            if row[self.columns['torrent_id'].column_indices[0]] == torrent_id:
                self.liststore.remove(row.iter)
                # Force an update of the torrentview
                self.update()
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
                    log.debug('Unable to get iter from path: %s', ex)
                    continue

                child_row = self.treeview.get_model().convert_iter_to_child_iter(None, row)
                child_row = self.treeview.get_model().get_model().convert_iter_to_child_iter(child_row)
                if self.liststore.iter_is_valid(child_row):
                    try:
                        value = self.liststore.get_value(child_row, self.columns['torrent_id'].column_indices[0])
                    except Exception as ex:
                        log.debug('Unable to get value from row: %s', ex)
                    else:
                        torrent_ids.append(value)
            if len(torrent_ids) == 0:
                return []

            return torrent_ids
        except ValueError:
            return []

    def get_torrent_status(self, torrent_id):
        """Returns data stored in self.torrents_state.status, it may not be complete"""
        return self.torrents_state.status.get(torrent_id, {})

    def get_visible_torrents(self):
        return list(self.torrents_state.visible_torrents)

    # Callbacks #
    def on_button_press_event(self, widget, event):
        """This is a callback for showing the right-click context menu."""
        log.debug('on_button_press_event')
        # We only care about right-clicks
        if event.button == 3:
            x, y = event.get_coords()
            path = self.treeview.get_path_at_pos(int(x), int(y))
            if not path:
                return
            row = self.model_filter.get_iter(path[0])

            if self.get_selected_torrents():
                if (self.model_filter.get_value(row, self.columns['torrent_id'].column_indices[0])
                        not in self.get_selected_torrents()):
                    self.treeview.get_selection().unselect_all()
                    self.treeview.get_selection().select_iter(row)
            else:
                self.treeview.get_selection().select_iter(row)
            torrentmenu = component.get('MenuBar').torrentmenu
            torrentmenu.popup(None, None, None, event.button, event.time)
            return True

    def on_selection_changed(self, treeselection):
        """This callback is know when the selection has changed."""
        log.debug('on_selection_changed')
        component.get('TorrentDetails').update()
        component.get('MenuBar').update_menu()

    def on_drag_drop(self, widget, drag_context, x, y, timestamp):
        widget.stop_emission('drag-drop')

    def on_drag_data_received(self, widget, drag_context, x, y, selection_data, info, timestamp):
        widget.stop_emission('drag_data_received')

    def on_columns_changed_event(self, treeview):
        log.debug('Treeview Columns Changed')
        self.save_state()

    def on_torrentadded_event(self, torrent_id, from_state):
        self.add_rows([torrent_id])
        self.update(from_cache=False)

    def on_torrentremoved_event(self, torrent_id):
        self.remove_row(torrent_id)
        self.torrents_state.status.pop(torrent_id, None)

    def on_sessionpaused_event(self):
        self.update()

    def on_sessionresumed_event(self):
        self.update()

    def on_torrentqueuechanged_event(self):
        self.update()

    # Handle keyboard shortcuts
    def on_key_press_event(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname is not None:
            func = getattr(self, 'keypress_' + keyname.lower(), None)
            if func:
                return func(event)

    def keypress_delete(self, event):
        log.debug('keypress_delete')
        torrents = self.get_selected_torrents()
        if torrents:
            if event.state & gtk.gdk.SHIFT_MASK:
                RemoveTorrentDialog(torrents, delete_files=True).run()
            else:
                RemoveTorrentDialog(torrents).run()

    def keypress_menu(self, event):
        log.debug('keypress_menu')
        if not self.get_selected_torrent():
            return

        torrentmenu = component.get('MenuBar').torrentmenu
        torrentmenu.popup(None, None, None, 3, event.time)
        return True
