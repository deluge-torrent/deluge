#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
import webbrowser

from gi.repository.Gdk import EventType
from gi.repository.Gtk import (
    CellRendererText,
    ListStore,
    SortType,
    TreeView,
    TreeViewColumn,
)

import deluge.component as component
from deluge.common import anchorify_urls, is_url
from deluge.decorators import maybe_coroutine
from deluge.ui.client import client

from .tab_data_funcs import ftranslate
from .torrentdetails import Tab

log = logging.getLogger(__name__)


class TrackersTab(Tab):
    def __init__(self):
        super().__init__('Trackers', 'trackers_tab', 'trackers_tab_label')

        self.trackers_menu = self.main_builder.get_object('menu_trackers_tab')
        component.get('MainWindow').connect_signals(self)

        self.listview: TreeView = self.main_builder.get_object('trackers_listview')
        self.listview.props.has_tooltip = True
        self.listview.connect('button-press-event', self._on_button_press_event)
        self.listview.connect('row-activated', self._on_row_activated)
        self.listview.props.activate_on_single_click = True

        # url, status, peers, message
        self.liststore = ListStore(str, str, int, str)

        # key is url, item is row iter
        self.trackers = {}

        self._can_get_trackers_info = False

        # self.treeview.append_column(
        #     Gtk.TreeViewColumn(_('Tier'), Gtk.CellRendererText(), text=0)
        # )
        column = TreeViewColumn(_('Tracker'))
        render = CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, 'text', 0)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(150)
        column.set_reorderable(True)
        self.listview.append_column(column)

        column = TreeViewColumn(_('Status'))
        render = CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, 'markup', 1)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(50)
        column.set_reorderable(True)
        self.listview.append_column(column)

        column = TreeViewColumn(_('Peers'))
        render = CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, 'text', 2)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(50)
        column.set_reorderable(True)
        self.listview.append_column(column)

        column = TreeViewColumn(_('Message'))
        render = CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, 'markup', 3)
        column.set_clickable(True)
        column.set_resizable(True)
        column.set_expand(False)
        column.set_min_width(100)
        column.set_reorderable(True)
        self.listview.append_column(column)

        self.listview.set_model(self.liststore)
        self.liststore.set_sort_column_id(0, SortType.ASCENDING)

        self.torrent_id = None

    def update(self):
        if client.is_standalone():
            self._can_get_trackers_info = True
        else:
            self._can_get_trackers_info = client.daemon_version_check_min('2.1.2')
        self.do_update()

    @maybe_coroutine
    async def do_update(self):
        # Get the first selected torrent
        torrent_id = component.get('TorrentView').get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if torrent_id:
            torrent_id = torrent_id[0]
        else:
            self.liststore.clear()
            return

        if torrent_id != self.torrent_id:
            # We only want to do this if the torrent_id has changed
            self.liststore.clear()
            self.trackers = {}
            self.torrent_id = torrent_id

        session = component.get('SessionProxy')

        if not self._can_get_trackers_info:
            tracker_keys = [
                'tracker_host',
                'tracker_status',
            ]
        else:
            tracker_keys = [
                'trackers',
                'trackers_status',
                'trackers_peers',
            ]

        status = await session.get_torrent_status(torrent_id, tracker_keys)
        self._on_get_torrent_tracker_status(status)

    def _on_get_torrent_tracker_status(self, status):
        # Check to see if we got valid data from the core
        if not status:
            return

        if not self._can_get_trackers_info:
            status['trackers'] = [{'url': status['tracker_host'], 'message': ''}]
            status['trackers_status'] = {
                status['tracker_host']: {
                    'status': status['tracker_status'],
                    'message': '',
                }
            }
            status['trackers_peers'] = {}

        new_trackers = set()
        for tracker in status['trackers']:
            new_trackers.add(tracker['url'])
            tracker_url = tracker['url']
            stacker_status_dict = status['trackers_status'].get(tracker_url, {})
            tracker_status = ftranslate(stacker_status_dict.get('status', ''))
            tracker_status = anchorify_urls(tracker_status, as_hyperlink=False)
            tracker_status_message = ftranslate(stacker_status_dict.get('message', ''))
            tracker_status_message = anchorify_urls(
                tracker_status_message, as_hyperlink=False
            )
            tracker_peers = status['trackers_peers'].get(tracker_url, 0)
            tracker_message = tracker.get('message', '')
            if not tracker_message and tracker_status_message:
                tracker_message = tracker_status_message
            if tracker_url in self.trackers:
                row = self.trackers[tracker_url]
                if not self.liststore.iter_is_valid(row):
                    # This iter is invalid, delete it and continue to next iteration
                    del self.trackers[tracker_url]
                    continue
                values = self.liststore.get(row, 1, 2, 3)
                if tracker_status != values[0]:
                    self.liststore.set_value(row, 1, tracker_status)
                if tracker_peers != values[1]:
                    self.liststore.set_value(row, 2, tracker_peers)
                if tracker_message != values[2]:
                    self.liststore.set_value(row, 3, tracker_message)
            else:
                row = self.liststore.append(
                    [
                        tracker_url,
                        tracker_status,
                        tracker_peers,
                        tracker_message,
                    ]
                )

                self.trackers[tracker_url] = row

        # Now we need to remove any tracker that were not in status['trackers'] list
        for tracker in set(self.trackers).difference(new_trackers):
            self.liststore.remove(self.trackers[tracker])
            del self.trackers[tracker]

    def clear(self):
        self.liststore.clear()

    def _on_button_press_event(self, widget, event):
        """This is a callback for handling click events."""
        log.debug('on_button_press_event')
        if event.button == 3:
            self.trackers_menu.popup(None, None, None, None, event.button, event.time)
            return True
        elif event.type == EventType.DOUBLE_BUTTON_PRESS:
            self.on_menuitem_edit_trackers_activate(event.button)

    def _on_row_activated(self, treeview, path, column):
        """THis is a callback for handling link click"""
        log.debug('on_row_activated')
        model = treeview.get_model()
        tree_iter = model.get_iter(path)

        # Get the index of the clicked column from the TreeViewColumn
        clicked_column_index = self._get_column_index(column)
        if clicked_column_index is None:
            log.warning(f'column {column.get_title()} not selected')
            return

        # Retrieve the value from the correct column based on the clicked column
        cell_value = model.get_value(tree_iter, clicked_column_index)

        if '<span' in cell_value:
            start_index = cell_value.index('>') + 1
            end_index = cell_value[start_index:].index('<') + start_index
            url = cell_value[start_index:end_index]
            if is_url(url):
                webbrowser.open_new(url)

    def _get_column_index(self, column):
        for index, col in enumerate(self.listview.get_columns()):
            if col == column:
                return index
        return None

    def on_menuitem_edit_trackers_activate(self, button):
        torrent_id = component.get('TorrentView').get_selected_torrent()
        if torrent_id:
            from .edittrackersdialog import EditTrackersDialog

            dialog = EditTrackersDialog(torrent_id, component.get('MainWindow').window)
            dialog.run()
