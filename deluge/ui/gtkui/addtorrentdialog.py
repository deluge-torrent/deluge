# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import division, unicode_literals

import logging
import os
from base64 import b64decode, b64encode
from xml.sax.saxutils import escape as xml_escape
from xml.sax.saxutils import unescape as xml_unescape

import gtk
from gobject import TYPE_INT64, TYPE_UINT64

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.httpdownloader import download_file
from deluge.ui.client import client
from deluge.ui.common import TorrentInfo
from deluge.ui.gtkui.common import get_clipboard_text, listview_replace_treestore, reparent_iter
from deluge.ui.gtkui.dialogs import ErrorDialog
from deluge.ui.gtkui.edittrackersdialog import trackers_tiers_from_text
from deluge.ui.gtkui.path_chooser import PathChooser
from deluge.ui.gtkui.torrentview_data_funcs import cell_data_size

log = logging.getLogger(__name__)


class AddTorrentDialog(component.Component):
    def __init__(self):
        component.Component.__init__(self, 'AddTorrentDialog')
        self.builder = gtk.Builder()
        # The base dialog
        self.builder.add_from_file(deluge.common.resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'add_torrent_dialog.ui')
        ))
        # The infohash dialog
        self.builder.add_from_file(deluge.common.resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'add_torrent_dialog.infohash.ui')
        ))
        # The url dialog
        self.builder.add_from_file(deluge.common.resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'add_torrent_dialog.url.ui')
        ))

        self.dialog = self.builder.get_object('dialog_add_torrent')

        self.dialog.connect('delete-event', self._on_delete_event)

        self.builder.connect_signals(self)

        # download?, path, filesize, sequence number, inconsistent?
        self.files_treestore = gtk.TreeStore(
            bool, str, TYPE_UINT64, TYPE_INT64, bool, str)
        self.files_treestore.set_sort_column_id(1, gtk.SORT_ASCENDING)

        # Holds the files info
        self.files = {}
        self.infos = {}
        self.core_config = {}
        self.options = {}

        self.previous_selected_torrent = None

        self.listview_torrents = self.builder.get_object('listview_torrents')
        self.listview_files = self.builder.get_object('listview_files')

        render = gtk.CellRendererText()
        render.connect('edited', self._on_torrent_name_edit)
        render.set_property('editable', True)
        column = gtk.TreeViewColumn(_('Torrent'), render, text=1)
        self.listview_torrents.append_column(column)

        render = gtk.CellRendererToggle()
        render.connect('toggled', self._on_file_toggled)
        column = gtk.TreeViewColumn(None, render, active=0, inconsistent=4)
        self.listview_files.append_column(column)

        column = gtk.TreeViewColumn(_('Filename'))
        render = gtk.CellRendererPixbuf()
        column.pack_start(render, False)
        column.add_attribute(render, 'stock-id', 5)
        render = gtk.CellRendererText()
        render.set_property('editable', True)
        render.connect('edited', self._on_filename_edited)
        column.pack_start(render, True)
        column.add_attribute(render, 'text', 1)
        column.set_expand(True)
        self.listview_files.append_column(column)

        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_('Size'))
        column.pack_start(render, True)
        column.set_cell_data_func(render, cell_data_size, 2)
        self.listview_files.append_column(column)

        self.torrent_liststore = gtk.ListStore(str, str, str)
        self.listview_torrents.set_model(self.torrent_liststore)
        self.listview_torrents.set_tooltip_column(2)
        self.listview_files.set_model(self.files_treestore)

        self.listview_files.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.listview_torrents.get_selection().connect('changed', self._on_torrent_changed)

        self.setup_move_completed_path_chooser()
        self.setup_download_location_path_chooser()

        # Get default config values from the core
        self.core_keys = [
            'pre_allocate_storage',
            'max_connections_per_torrent',
            'max_upload_slots_per_torrent',
            'max_upload_speed_per_torrent',
            'max_download_speed_per_torrent',
            'prioritize_first_last_pieces',
            'sequential_download',
            'add_paused',
            'download_location',
            'download_location_paths_list',
            'move_completed',
            'move_completed_path',
            'move_completed_paths_list',
        ]
        # self.core_keys += self.move_completed_path_chooser.get_config_keys()
        self.builder.get_object('notebook1').connect('switch-page', self._on_switch_page)

    def start(self):
        self.update_core_config()

    def show(self, focus=False):
        return self.update_core_config(True, focus)

    def _show(self, focus=False):
        if component.get('MainWindow').is_on_active_workspace():
            self.dialog.set_transient_for(component.get('MainWindow').window)
        else:
            self.dialog.set_transient_for(None)

        self.dialog.present()
        if focus:
            self.dialog.window.focus()

        return None

    def hide(self):
        self.dialog.hide()
        self.files = {}
        self.infos = {}
        self.options = {}
        self.previous_selected_torrent = None
        self.torrent_liststore.clear()
        self.files_treestore.clear()
        self.dialog.set_transient_for(component.get('MainWindow').window)
        return None

    def update_core_config(self, show=False, focus=False):
        def _on_config_values(config):
            self.core_config = config
            if self.core_config:
                self.set_default_options()
            if show:
                self._show(focus)

        # Send requests to the core for these config values
        return client.core.get_config_values(self.core_keys).addCallback(_on_config_values)

    def add_from_files(self, filenames):
        new_row = None
        already_added = 0

        for filename in filenames:
            # Get the torrent data from the torrent file
            try:
                info = TorrentInfo(filename)
            except Exception as ex:
                log.debug('Unable to open torrent file: %s', ex)
                ErrorDialog(_('Invalid File'), ex, self.dialog).run()
                continue

            if info.info_hash in self.files:
                already_added += 1
                continue

            new_row = self.torrent_liststore.append([info.info_hash, info.name, xml_escape(filename)])
            self.files[info.info_hash] = info.files
            self.infos[info.info_hash] = info.filedata
            self.listview_torrents.get_selection().select_iter(new_row)

            self.set_default_options()
            self.save_torrent_options(new_row)

        (model, row) = self.listview_torrents.get_selection().get_selected()
        if not row and new_row:
            self.listview_torrents.get_selection().select_iter(new_row)

        self.dialog.set_title(_('Add Torrents (%d)') % len(self.torrent_liststore))

        if already_added:
            log.debug('Tried to add %d duplicate torrents!', already_added)
            ErrorDialog(
                _('Duplicate Torrent(s)'),
                _('You cannot add the same torrent twice. %d torrents were already added.' % already_added),
                self.dialog
            ).run()

    def add_from_magnets(self, uris):
        new_row = None

        for uri in uris:
            magnet = deluge.common.get_magnet_info(uri)
            if not magnet:
                log.error('Invalid magnet: %s', uri)
                continue
            elif magnet['info_hash'] in self.infos:
                log.info('Torrent already in Add Dialog list: %s', uri)
                continue

            new_row = self.torrent_liststore.append([magnet['info_hash'], magnet['name'], xml_escape(uri)])
            self.files[magnet['info_hash']] = magnet['files_tree']
            self.infos[magnet['info_hash']] = None

            def on_uri_metadata(result, uri):
                info_hash, b64_metadata = result
                log.debug('on_uri_metadata for %s (%s)', uri, info_hash)

                if b64_metadata:
                    metadata = b64decode(b64_metadata)
                    info = TorrentInfo(metadata=metadata)
                    self.files[info_hash] = info.files
                    self.infos[info_hash] = info.filedata
                else:
                    log.info('Unable to fetch metadata for magnet: %s', uri)

            client.core.prefetch_magnet_metadata(uri).addCallback(on_uri_metadata, uri)

            self.listview_torrents.get_selection().select_iter(new_row)
            self.set_default_options()
            self.save_torrent_options(new_row)

        (model, row) = self.listview_torrents.get_selection().get_selected()
        if not row and new_row:
            self.listview_torrents.get_selection().select_iter(new_row)

    def _on_torrent_changed(self, treeselection):
        (model, row) = treeselection.get_selected()
        if row is None or not model.iter_is_valid(row):
            self.files_treestore.clear()
            self.previous_selected_torrent = None
            return

        if model[row][0] not in self.files:
            self.files_treestore.clear()
            self.previous_selected_torrent = None
            return

        # Save the previous torrents options
        self.save_torrent_options()
        # Update files list
        files_list = self.files[model.get_value(row, 0)]

        self.prepare_file_store(files_list)

        if self.core_config == {}:
            self.update_core_config()

        # Update the options frame
        self.update_torrent_options(model.get_value(row, 0))

        self.previous_selected_torrent = row

    def _on_torrent_name_edit(self, w, row, new_name):
        # TODO: Update torrent name
        pass

    def _on_switch_page(self, widget, page, page_num):
        # Save the torrent options when switching notebook pages
        self.save_torrent_options()

    def prepare_file_store(self, files):
        with listview_replace_treestore(self.listview_files):
            split_files = {}
            for idx, _file in enumerate(files):
                self.prepare_file(
                    _file, _file['path'], idx, _file.get('download', True), split_files
                )
            self.add_files(None, split_files)
        self.listview_files.expand_row(b'0', False)

    def prepare_file(self, _file, file_name, file_num, download, files_storage):
        first_slash_index = file_name.find(os.path.sep)
        if first_slash_index == -1:
            files_storage[file_name] = (file_num, _file, download)
        else:
            file_name_chunk = file_name[:first_slash_index + 1]
            if file_name_chunk not in files_storage:
                files_storage[file_name_chunk] = {}
            self.prepare_file(_file, file_name[first_slash_index + 1:],
                              file_num, download, files_storage[file_name_chunk])

    def add_files(self, parent_iter, split_files):
        ret = 0
        for key, value in split_files.items():
            if key.endswith(os.path.sep):
                chunk_iter = self.files_treestore.append(
                    parent_iter, [True, key, 0, -1, False, gtk.STOCK_DIRECTORY])
                chunk_size = self.add_files(chunk_iter, value)
                self.files_treestore.set(chunk_iter, 2, chunk_size)
                ret += chunk_size
            else:
                self.files_treestore.append(parent_iter, [
                    value[2], key, value[1]['size'],
                    value[0], False, gtk.STOCK_FILE
                ])
                ret += value[1]['size']
        if parent_iter and self.files_treestore.iter_has_child(parent_iter):
            # Iterate through the children and see what we should label the
            # folder, download true, download false or inconsistent.
            itr = self.files_treestore.iter_children(parent_iter)
            download = []
            download_value = False
            inconsistent = False
            while itr:
                download.append(self.files_treestore.get_value(itr, 0))
                itr = self.files_treestore.iter_next(itr)

            if sum(download) == len(download):
                download_value = True
            elif sum(download) == 0:
                download_value = False
            else:
                inconsistent = True

            self.files_treestore.set_value(parent_iter, 0, download_value)
            self.files_treestore.set_value(parent_iter, 4, inconsistent)
        return ret

    def load_path_choosers_data(self):
        self.move_completed_path_chooser.set_text(self.core_config['move_completed_path'],
                                                  cursor_end=False, default_text=True)
        self.download_location_path_chooser.set_text(self.core_config['download_location'],
                                                     cursor_end=False, default_text=True)
        self.builder.get_object('chk_move_completed').set_active(self.core_config['move_completed'])

    def setup_move_completed_path_chooser(self):
        self.move_completed_hbox = self.builder.get_object('hbox_move_completed_chooser')
        self.move_completed_path_chooser = PathChooser('move_completed_paths_list')
        self.move_completed_hbox.add(self.move_completed_path_chooser)
        self.move_completed_hbox.show_all()

    def setup_download_location_path_chooser(self):
        self.download_location_hbox = self.builder.get_object('hbox_download_location_chooser')
        self.download_location_path_chooser = PathChooser('download_location_paths_list')
        self.download_location_hbox.add(self.download_location_path_chooser)
        self.download_location_hbox.show_all()

    def update_torrent_options(self, torrent_id):
        if torrent_id not in self.options:
            self.set_default_options()
            return

        options = self.options[torrent_id]

        self.download_location_path_chooser.set_text(options['download_location'], cursor_end=True)
        self.move_completed_path_chooser.set_text(options['move_completed_path'], cursor_end=True)

        self.builder.get_object('spin_maxdown').set_value(
            options['max_download_speed'])
        self.builder.get_object('spin_maxup').set_value(
            options['max_upload_speed'])
        self.builder.get_object('spin_maxconnections').set_value(
            options['max_connections'])
        self.builder.get_object('spin_maxupslots').set_value(
            options['max_upload_slots'])
        self.builder.get_object('chk_paused').set_active(
            options['add_paused'])
        self.builder.get_object('chk_pre_alloc').set_active(
            options['pre_allocate_storage'])
        self.builder.get_object('chk_prioritize').set_active(
            options['prioritize_first_last_pieces'])
        self.builder.get_object('chk_sequential_download').set_active(
            options['sequential_download'])
        self.builder.get_object('chk_move_completed').set_active(
            options['move_completed'])

    def save_torrent_options(self, row=None):
        # Keeps the torrent options dictionary up-to-date with what the user has
        # selected.
        if row is None:
            if self.previous_selected_torrent and \
                    self.torrent_liststore.iter_is_valid(self.previous_selected_torrent):
                row = self.previous_selected_torrent
            else:
                return

        torrent_id = self.torrent_liststore.get_value(row, 0)

        if torrent_id in self.options:
            options = self.options[torrent_id]
        else:
            options = {}

        options['download_location'] = self.download_location_path_chooser.get_text()
        options['move_completed_path'] = self.move_completed_path_chooser.get_text()
        options['pre_allocate_storage'] = self.builder.get_object('chk_pre_alloc').get_active()
        options['move_completed'] = self.builder.get_object('chk_move_completed').get_active()
        options['max_download_speed'] = self.builder.get_object('spin_maxdown').get_value()
        options['max_upload_speed'] = self.builder.get_object('spin_maxup').get_value()
        options['max_connections'] = self.builder.get_object('spin_maxconnections').get_value_as_int()
        options['max_upload_slots'] = self.builder.get_object('spin_maxupslots').get_value_as_int()
        options['add_paused'] = self.builder.get_object('chk_paused').get_active()
        options['prioritize_first_last_pieces'] = self.builder.get_object('chk_prioritize').get_active()
        options['sequential_download'] = self.builder.get_object(
            'chk_sequential_download').get_active() or False
        options['move_completed'] = self.builder.get_object('chk_move_completed').get_active()
        options['seed_mode'] = self.builder.get_object('chk_seed_mode').get_active()

        self.options[torrent_id] = options

        # Save the file priorities
        files_priorities = self.build_priorities(
            self.files_treestore.get_iter_first(), {}
        )

        if len(files_priorities) > 0:
            for i, file_dict in enumerate(self.files[torrent_id]):
                file_dict['download'] = files_priorities[i]

    def build_priorities(self, _iter, priorities):
        while _iter is not None:
            if self.files_treestore.iter_has_child(_iter):
                self.build_priorities(self.files_treestore.iter_children(_iter), priorities)
            elif not self.files_treestore.get_value(_iter, 1).endswith(os.path.sep):
                priorities[self.files_treestore.get_value(_iter, 3)] = self.files_treestore.get_value(_iter, 0)
            _iter = self.files_treestore.iter_next(_iter)
        return priorities

    def set_default_options(self):
        if not self.core_config:
            # update_core_config will call this method again.
            self.update_core_config()
            return

        self.load_path_choosers_data()

        self.builder.get_object('chk_pre_alloc').set_active(
            self.core_config['pre_allocate_storage'])
        self.builder.get_object('spin_maxdown').set_value(
            self.core_config['max_download_speed_per_torrent'])
        self.builder.get_object('spin_maxup').set_value(
            self.core_config['max_upload_speed_per_torrent'])
        self.builder.get_object('spin_maxconnections').set_value(
            self.core_config['max_connections_per_torrent'])
        self.builder.get_object('spin_maxupslots').set_value(
            self.core_config['max_upload_slots_per_torrent'])
        self.builder.get_object('chk_paused').set_active(
            self.core_config['add_paused'])
        self.builder.get_object('chk_prioritize').set_active(
            self.core_config['prioritize_first_last_pieces'])
        self.builder.get_object('chk_sequential_download').set_active(
            self.core_config['sequential_download'])
        self.builder.get_object('chk_move_completed').set_active(
            self.core_config['move_completed'])
        self.builder.get_object('chk_seed_mode').set_active(False)

    def get_file_priorities(self, torrent_id):
        # A list of priorities
        files_list = []

        for file_dict in self.files[torrent_id]:
            if not file_dict['download']:
                files_list.append(0)
            else:
                files_list.append(1)

        return files_list

    def _on_file_toggled(self, render, path):
        (model, paths) = self.listview_files.get_selection().get_selected_rows()
        if len(paths) > 1:
            for path in paths:
                row = model.get_iter(path)
                self.toggle_iter(row)
        else:
            row = model.get_iter(path)
            self.toggle_iter(row)
        self.update_treeview_toggles(self.files_treestore.get_iter_first())

    def toggle_iter(self, _iter, toggle_to=None):
        if toggle_to is None:
            toggle_to = not self.files_treestore.get_value(_iter, 0)
        self.files_treestore.set_value(_iter, 0, toggle_to)
        if self.files_treestore.iter_has_child(_iter):
            child = self.files_treestore.iter_children(_iter)
            while child is not None:
                self.toggle_iter(child, toggle_to)
                child = self.files_treestore.iter_next(child)

    def update_treeview_toggles(self, _iter):
        toggle_inconsistent = -1
        this_level_toggle = None
        while _iter is not None:
            if self.files_treestore.iter_has_child(_iter):
                toggle = self.update_treeview_toggles(self.files_treestore.iter_children(_iter))
                if toggle == toggle_inconsistent:
                    self.files_treestore.set_value(_iter, 4, True)
                else:
                    self.files_treestore.set_value(_iter, 0, toggle)
                    # set inconsistent to false
                    self.files_treestore.set_value(_iter, 4, False)
            else:
                toggle = self.files_treestore.get_value(_iter, 0)
            if this_level_toggle is None:
                this_level_toggle = toggle
            elif this_level_toggle != toggle:
                this_level_toggle = toggle_inconsistent
            _iter = self.files_treestore.iter_next(_iter)
        return this_level_toggle

    def on_button_file_clicked(self, widget):
        log.debug('on_button_file_clicked')
        # Setup the filechooserdialog
        chooser = gtk.FileChooserDialog(
            _('Choose a .torrent file'),
            None,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN,
                     gtk.RESPONSE_OK)
        )

        chooser.set_transient_for(self.dialog)
        chooser.set_select_multiple(True)
        chooser.set_property('skip-taskbar-hint', True)
        chooser.set_local_only(False)

        # Add .torrent and * file filters
        file_filter = gtk.FileFilter()
        file_filter.set_name(_('Torrent files'))
        file_filter.add_pattern('*.' + 'torrent')
        chooser.add_filter(file_filter)
        file_filter = gtk.FileFilter()
        file_filter.set_name(_('All files'))
        file_filter.add_pattern('*')
        chooser.add_filter(file_filter)

        # Load the 'default_load_path' from the config
        self.config = ConfigManager('gtkui.conf')
        if self.config['default_load_path'] is not None:
            chooser.set_current_folder(self.config['default_load_path'])

        # Run the dialog
        response = chooser.run()

        if response == gtk.RESPONSE_OK:
            result = chooser.get_filenames()
            self.config['default_load_path'] = chooser.get_current_folder()
        else:
            chooser.destroy()
            return

        chooser.destroy()
        self.add_from_files(result)

    def on_button_url_clicked(self, widget):
        log.debug('on_button_url_clicked')
        dialog = self.builder.get_object('url_dialog')
        entry = self.builder.get_object('entry_url')

        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_transient_for(self.dialog)
        entry.grab_focus()

        text = get_clipboard_text()
        if text and deluge.common.is_url(text) or deluge.common.is_magnet(text):
            entry.set_text(text)

        dialog.show_all()
        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            url = entry.get_text().decode('utf-8')
        else:
            url = None

        entry.set_text('')
        dialog.hide()

        # This is where we need to fetch the .torrent file from the URL and
        # add it to the list.
        log.debug('url: %s', url)
        if url:
            if deluge.common.is_url(url):
                self.add_from_url(url)
            elif deluge.common.is_magnet(url):
                self.add_from_magnets([url])
            else:
                ErrorDialog(
                    _('Invalid URL'),
                    '%s %s' % (url, _('is not a valid URL.')),
                    self.dialog
                ).run()

    def add_from_url(self, url):
        dialog = gtk.Dialog(
            _('Downloading...'),
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
            parent=self.dialog)
        dialog.set_transient_for(self.dialog)

        pb = gtk.ProgressBar()
        dialog.vbox.pack_start(pb, True, True, 0)
        dialog.show_all()

        # Create a tmp file path
        import tempfile
        tmp_fd, tmp_file = tempfile.mkstemp(prefix='deluge_url.', suffix='.torrent')

        def on_part(data, current_length, total_length):
            if total_length:
                percent = current_length / total_length
                pb.set_fraction(percent)
                pb.set_text('%.2f%% (%s / %s)' % (
                    percent * 100,
                    deluge.common.fsize(current_length),
                    deluge.common.fsize(total_length)))
            else:
                pb.pulse()
                pb.set_text('%s' % deluge.common.fsize(current_length))

        def on_download_success(result):
            self.add_from_files([result])
            dialog.destroy()

        def on_download_fail(result):
            log.debug('Download failed: %s', result)
            dialog.destroy()
            ErrorDialog(
                _('Download Failed'), '%s %s' % (_('Failed to download:'), url),
                details=result.getErrorMessage(), parent=self.dialog
            ).run()
            return result

        d = download_file(url, tmp_file, on_part)
        os.close(tmp_fd)
        d.addCallbacks(on_download_success, on_download_fail)

    def on_button_hash_clicked(self, widget):
        log.debug('on_button_hash_clicked')
        dialog = self.builder.get_object('dialog_infohash')
        entry = self.builder.get_object('entry_hash')
        textview = self.builder.get_object('text_trackers')

        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_transient_for(self.dialog)
        entry.grab_focus()

        text = get_clipboard_text()
        if deluge.common.is_infohash(text):
            entry.set_text(text)

        dialog.show_all()
        response = dialog.run()
        infohash = entry.get_text().strip()
        if response == gtk.RESPONSE_OK and deluge.common.is_infohash(infohash):
            # Create a list of trackers from the textview buffer
            tview_buf = textview.get_buffer()
            trackers_text = tview_buf.get_text(*tview_buf.get_bounds())
            log.debug('Create torrent tracker lines: %s', trackers_text)
            trackers = list(trackers_tiers_from_text(trackers_text).keys())

            # Convert the information to a magnet uri, this is just easier to
            # handle this way.
            log.debug('trackers: %s', trackers)
            magnet = deluge.common.create_magnet_uri(infohash, infohash, trackers)
            log.debug('magnet uri: %s', magnet)
            self.add_from_magnets([magnet])

        entry.set_text('')
        textview.get_buffer().set_text('')
        dialog.hide()

    def on_button_remove_clicked(self, widget):
        log.debug('on_button_remove_clicked')
        (model, row) = self.listview_torrents.get_selection().get_selected()
        if row is None:
            return

        torrent_id = model.get_value(row, 0)

        model.remove(row)
        del self.files[torrent_id]
        del self.infos[torrent_id]
        self.dialog.set_title(_('Add Torrents (%d)') % len(self.torrent_liststore))

    def on_button_trackers_clicked(self, widget):
        log.debug('on_button_trackers_clicked')

    def on_button_cancel_clicked(self, widget):
        log.debug('on_button_cancel_clicked')
        self.hide()

    def on_button_add_clicked(self, widget):
        log.debug('on_button_add_clicked')
        self.add_torrents()
        self.hide()

    def add_torrents(self):
        (model, row) = self.listview_torrents.get_selection().get_selected()
        if row is not None:
            self.save_torrent_options(row)

        torrents_to_add = []

        row = self.torrent_liststore.get_iter_first()
        while row is not None:
            torrent_id = self.torrent_liststore.get_value(row, 0)
            filename = xml_unescape(self.torrent_liststore.get_value(row, 2))
            try:
                options = self.options[torrent_id]
            except KeyError:
                options = None

            file_priorities = self.get_file_priorities(torrent_id)
            if options is not None:
                options['file_priorities'] = file_priorities

            try:
                filedump = b64encode(self.infos[torrent_id])
            except TypeError:
                filedump = None

            if deluge.common.is_magnet(filename):
                client.core.add_torrent_magnet(filename, options, filedump=filedump)
            else:
                torrents_to_add.append((os.path.split(filename)[-1], filedump, options))
            row = self.torrent_liststore.iter_next(row)

        def on_torrents_added(errors):
            if errors:
                log.info('Failed to add %d out of %d torrents.', len(errors), len(torrents_to_add))
                for e in errors:
                    log.info('Torrent add failed: %s', e)
            else:
                log.info('Successfully added %d torrents.', len(torrents_to_add))
        client.core.add_torrent_files(torrents_to_add).addCallback(on_torrents_added)

    def on_button_apply_clicked(self, widget):
        log.debug('on_button_apply_clicked')
        (model, row) = self.listview_torrents.get_selection().get_selected()
        if row is None:
            return

        self.save_torrent_options(row)

        # The options, except file renames, we want all the torrents to have
        options = self.options[model.get_value(row, 0)].copy()
        options.pop('mapped_files', None)

        # Set all the torrent options
        row = model.get_iter_first()
        while row is not None:
            torrent_id = model.get_value(row, 0)
            self.options[torrent_id].update(options)
            row = model.iter_next(row)

    def on_button_revert_clicked(self, widget):
        log.debug('on_button_revert_clicked')
        (model, row) = self.listview_torrents.get_selection().get_selected()
        if row is None:
            return

        del self.options[model.get_value(row, 0)]
        self.set_default_options()

    def on_chk_move_completed_toggled(self, widget):
        value = widget.get_active()
        self.move_completed_path_chooser.set_sensitive(value)

    def _on_delete_event(self, widget, event):
        self.hide()
        return True

    def get_file_path(self, row, path=''):
        if not row:
            return path

        path = self.files_treestore[row][1] + path
        return self.get_file_path(self.files_treestore.iter_parent(row), path)

    def _on_filename_edited(self, renderer, path, new_text):
        index = self.files_treestore[path][3]

        new_text = new_text.strip(os.path.sep).strip()

        # Return if the text hasn't changed
        if new_text == self.files_treestore[path][1]:
            return

        # Get the tree iter
        itr = self.files_treestore.get_iter(path)

        # Get the torrent_id
        (model, row) = self.listview_torrents.get_selection().get_selected()
        torrent_id = model[row][0]

        if 'mapped_files' not in self.options[torrent_id]:
            self.options[torrent_id]['mapped_files'] = {}

        if index > -1:
            # We're renaming a file! Yay! That's easy!
            if not new_text:
                return
            parent = self.files_treestore.iter_parent(itr)
            file_path = os.path.join(self.get_file_path(parent), new_text)
            # Don't rename if filename exists
            if parent:
                for row in self.files_treestore[parent].iterchildren():
                    if new_text == row[1]:
                        return
            if os.path.sep in new_text:
                # There are folders in this path, so we need to create them
                # and then move the file iter to top
                split_text = new_text.split(os.path.sep)
                for s in split_text[:-1]:
                    parent = self.files_treestore.append(parent, [True, s, 0, -1, False, gtk.STOCK_DIRECTORY])

                self.files_treestore[itr][1] = split_text[-1]
                reparent_iter(self.files_treestore, itr, parent)
            else:
                # Update the row's text
                self.files_treestore[itr][1] = new_text

            # Update the mapped_files dict in the options with the index and new
            # file path.
            # We'll send this to the core when adding the torrent so it knows
            # what to rename before adding.
            self.options[torrent_id]['mapped_files'][index] = file_path
            self.files[torrent_id][index]['path'] = file_path
        else:
            # Folder!
            def walk_tree(row):
                if not row:
                    return

                # Get the file path base once, since it will be the same for
                # all siblings
                file_path_base = self.get_file_path(
                    self.files_treestore.iter_parent(row)
                )

                # Iterate through all the siblings at this level
                while row:
                    # We recurse if there are children
                    if self.files_treestore.iter_has_child(row):
                        walk_tree(self.files_treestore.iter_children(row))

                    index = self.files_treestore[row][3]

                    if index > -1:
                        # Get the new full path for this file
                        file_path = file_path_base + self.files_treestore[row][1]

                        # Update the file path in the mapped_files dict
                        self.options[torrent_id]['mapped_files'][index] = file_path
                        self.files[torrent_id][index]['path'] = file_path

                    # Get the next siblings iter
                    row = self.files_treestore.iter_next(row)

            # Update the treestore row first so that when walking the tree
            # we can construct the new proper paths

            # We need to check if this folder has been split
            if os.path.sep in new_text:
                # It's been split, so we need to add new folders and then re-parent
                # itr.
                parent = self.files_treestore.iter_parent(itr)
                split_text = new_text.split(os.path.sep)
                for s in split_text[:-1]:
                    # We don't iterate over the last item because we'll just use
                    # the existing itr and change the text
                    parent = self.files_treestore.append(parent, [
                        True, s + os.path.sep, 0, -1, False, gtk.STOCK_DIRECTORY
                    ])

                self.files_treestore[itr][1] = split_text[-1] + os.path.sep

                # Now re-parent itr to parent
                reparent_iter(self.files_treestore, itr, parent)
                itr = parent

                # We need to re-expand the view because it might contracted
                # if we change the root iter
                self.listview_files.expand_row(b'0', False)
            else:
                # This was a simple folder rename without any splits, so just
                # change the path for itr
                self.files_treestore[itr][1] = new_text + os.path.sep

            # Walk through the tree from 'itr' and add all the new file paths
            # to the 'mapped_files' option
            walk_tree(itr)
