# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import division, unicode_literals

import logging
import os.path
from base64 import b64encode

from gi.repository import Gtk
from gi.repository.GObject import TYPE_UINT64, idle_add
from twisted.internet.threads import deferToThread

import deluge.component as component
from deluge.common import get_path_size, is_url, resource_filename
from deluge.configmanager import ConfigManager
from deluge.ui.client import client
from deluge.ui.gtkui.edittrackersdialog import last_tier_trackers_from_liststore, trackers_tiers_from_text
from deluge.ui.gtkui.torrentview_data_funcs import cell_data_size

log = logging.getLogger(__name__)


class CreateTorrentDialog(object):

    def __init__(self):
        pass

    def show(self):
        self.builder = Gtk.Builder()

        # The main dialog
        self.builder.add_from_file(resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'create_torrent_dialog.ui'),
        ))
        # The remote path dialog
        self.builder.add_from_file(resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'create_torrent_dialog.remote_path.ui'),
        ))
        # The remote save dialog
        self.builder.add_from_file(resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'create_torrent_dialog.remote_save.ui'),
        ))
        # The progress dialog
        self.builder.add_from_file(resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'create_torrent_dialog.progress.ui'),
        ))

        self.config = ConfigManager('gtkui.conf')

        self.dialog = self.builder.get_object('create_torrent_dialog')
        self.dialog.set_transient_for(component.get('MainWindow').window)

        self.builder.connect_signals(self)

        # path, icon, size
        self.files_treestore = Gtk.TreeStore(str, str, TYPE_UINT64)

        column = Gtk.TreeViewColumn(_('Filename'))
        render = Gtk.CellRendererPixbuf()
        column.pack_start(render, False)
        column.add_attribute(render, 'stock-id', 1)
        render = Gtk.CellRendererText()
        column.pack_start(render, True)
        column.add_attribute(render, 'text', 0)
        column.set_expand(True)
        self.builder.get_object('treeview_files').append_column(column)

        column = Gtk.TreeViewColumn(_('Size'))
        render = Gtk.CellRendererText()
        column.pack_start(render, True)
        column.set_cell_data_func(render, cell_data_size, 2)
        self.builder.get_object('treeview_files').append_column(column)

        self.builder.get_object('treeview_files').set_model(self.files_treestore)
        self.builder.get_object('treeview_files').set_show_expanders(False)

        # tier, url
        self.trackers_liststore = Gtk.ListStore(int, str)

        self.builder.get_object('tracker_treeview').append_column(
            Gtk.TreeViewColumn(_('Tier'), Gtk.CellRendererText(), text=0),
        )
        self.builder.get_object('tracker_treeview').append_column(
            Gtk.TreeViewColumn(_('Tracker'), Gtk.CellRendererText(), text=1),
        )

        self.builder.get_object('tracker_treeview').set_model(self.trackers_liststore)
        self.trackers_liststore.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        if not client.is_localhost() and client.connected():
            self.builder.get_object('button_remote_path').show()
        else:
            self.builder.get_object('button_remote_path').hide()

        self.dialog.show()

    def parse_piece_size_text(self, value):
        psize, metric = value.split()
        psize = int(psize)
        if psize < 32:
            # This is a MiB value
            psize = psize * 1024 * 1024
        else:
            # This is a KiB value
            psize = psize * 1024

        return psize

    def adjust_piece_size(self):
        """Adjusts the recommended piece based on the file/folder/path selected."""
        size = self.files_treestore[0][2]
        model = self.builder.get_object('combo_piece_size').get_model()
        for index, value in enumerate(model):
            psize = self.parse_piece_size_text(value[0])
            pieces = size // psize
            if pieces < 2048 or (index + 1) == len(model):
                self.builder.get_object('combo_piece_size').set_active(index)
                break

    def on_button_file_clicked(self, widget):
        log.debug('on_button_file_clicked')
        # Setup the filechooserdialog
        chooser = Gtk.FileChooserDialog(
            _('Choose a file'),
            self.dialog,
            Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        chooser.set_transient_for(self.dialog)
        chooser.set_select_multiple(False)
        chooser.set_property('skip-taskbar-hint', True)

        # Run the dialog
        response = chooser.run()

        if response == Gtk.ResponseType.OK:
            result = chooser.get_filename()
        else:
            chooser.destroy()
            return

        path = result.decode('utf-8')

        self.files_treestore.clear()
        self.files_treestore.append(None, [result, Gtk.STOCK_FILE, get_path_size(path)])
        self.adjust_piece_size()
        chooser.destroy()

    def on_button_folder_clicked(self, widget):
        log.debug('on_button_folder_clicked')
        # Setup the filechooserdialog
        chooser = Gtk.FileChooserDialog(
            _('Choose a folder'),
            self.dialog,
            Gtk.FileChooserAction.SELECT_FOLDER,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        chooser.set_transient_for(self.dialog)
        chooser.set_select_multiple(False)
        chooser.set_property('skip-taskbar-hint', True)
        # Run the dialog
        response = chooser.run()

        if response == Gtk.ResponseType.OK:
            result = chooser.get_filename()
        else:
            chooser.destroy()
            return

        path = result.decode('utf-8')

        self.files_treestore.clear()
        self.files_treestore.append(None, [result, Gtk.STOCK_OPEN, get_path_size(path)])
        self.adjust_piece_size()
        chooser.destroy()

    def on_button_remote_path_clicked(self, widget):
        log.debug('on_button_remote_path_clicked')
        dialog = self.builder.get_object('remote_path_dialog')
        entry = self.builder.get_object('entry_path')
        dialog.set_transient_for(self.dialog)
        entry.set_text('/')
        entry.grab_focus()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            result = entry.get_text()

            def _on_get_path_size(size):
                log.debug('size: %s', size)
                if size > 0:
                    self.files_treestore.clear()
                    self.files_treestore.append(None, [result, Gtk.STOCK_NETWORK, size])
                    self.adjust_piece_size()
            client.core.get_path_size(result).addCallback(_on_get_path_size)
            client.force_call(True)

        dialog.hide()

    def on_button_cancel_clicked(self, widget):
        log.debug('on_button_cancel_clicked')
        self.dialog.destroy()

    def on_button_save_clicked(self, widget):
        log.debug('on_button_save_clicked')
        if len(self.files_treestore) == 0:
            return

        # Get the path
        path = self.files_treestore[0][0].rstrip('\\/')
        torrent_filename = '%s.torrent' % os.path.split(path)[-1]

        is_remote = self.files_treestore[0][1] == Gtk.STOCK_NETWORK

        if is_remote:
            # This is a remote path
            dialog = self.builder.get_object('remote_save_dialog')
            dialog.set_transient_for(self.dialog)
            dialog_save_path = self.builder.get_object('entry_save_path')
            dialog_save_path.set_text(path + '.torrent')
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                result = dialog_save_path.get_text()
            else:
                dialog.hide()
                return
            dialog.hide()
        else:
            # Setup the filechooserdialog
            chooser = gtk.FileChooserDialog(
                _('Save .torrent file'), self.dialog,
                Gtk.FileChooserAction.SAVE,
                buttons=(
                    Gtk.STOCK_CANCEL,
                    Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_SAVE,
                    Gtk.ResponseType.OK,
                ),
            )

            chooser.set_transient_for(self.dialog)
            chooser.set_select_multiple(False)
            chooser.set_property('skip-taskbar-hint', True)

            # Add .torrent and * file filters
            file_filter = Gtk.FileFilter()
            file_filter.set_name(_('Torrent files'))
            file_filter.add_pattern('*.' + 'torrent')
            chooser.add_filter(file_filter)
            file_filter = Gtk.FileFilter()
            file_filter.set_name(_('All files'))
            file_filter.add_pattern('*')
            chooser.add_filter(file_filter)

            chooser.set_current_name(torrent_filename)
            # Run the dialog
            response = chooser.run()

            if response == Gtk.ResponseType.OK:
                result = chooser.get_filename()
            else:
                chooser.destroy()
                return
            chooser.destroy()

        # Fix up torrent filename
        if len(result) < 9:
            result += '.torrent'
        elif result[-8:] != '.torrent':
            result += '.torrent'

        # Get a list of trackers
        trackers = []
        if not len(self.trackers_liststore):
            tracker = None
        else:
            # Create a list of lists [[tier0, ...], [tier1, ...], ...]
            tier_dict = {}
            for tier, tracker in self.trackers_liststore:
                tier_dict.setdefault(tier, []).append(tracker)

            trackers = [tier_dict[tier] for tier in sorted(tier_dict)]
            # Get the first tracker in the first tier
            tracker = trackers[0][0]

        # Get a list of webseeds
        textview_buf = self.builder.get_object('textview_webseeds').get_buffer()
        lines = textview_buf.get_text(*textview_buf.get_bounds()).strip().split('\n')
        webseeds = []
        for line in lines:
            line = line.replace('\\', '/')  # Fix any mistyped urls.
            if is_url(line):
                webseeds.append(line)
        # Get the piece length in bytes
        combo = self.builder.get_object('combo_piece_size')
        piece_length = self.parse_piece_size_text(combo.get_model()[combo.get_active()][0])

        author = self.builder.get_object('entry_author').get_text()
        comment = self.builder.get_object('entry_comments').get_text()
        private = self.builder.get_object('chk_private_flag').get_active()
        add_to_session = self.builder.get_object('chk_add_to_session').get_active()

        if is_remote:
            def torrent_created():
                self.builder.get_object('progress_dialog').hide()
                client.deregister_event_handler('CreateTorrentProgressEvent', on_create_torrent_progress_event)

            def on_create_torrent_progress_event(piece_count, num_pieces):
                self._on_create_torrent_progress(piece_count, num_pieces)
                if piece_count == num_pieces:
                    from twisted.internet import reactor
                    reactor.callLater(0.5, torrent_created)

            client.register_event_handler('CreateTorrentProgressEvent', on_create_torrent_progress_event)

            client.core.create_torrent(
                path,
                tracker,
                piece_length,
                comment,
                result,
                webseeds,
                private,
                author,
                trackers,
                add_to_session,
            )

        else:

            def hide_progress(result):
                self.builder.get_object('progress_dialog').hide()

            deferToThread(
                self.create_torrent,
                path.decode('utf-8'),
                tracker,
                piece_length,
                self._on_create_torrent_progress,
                comment,
                result.decode('utf-8'),
                webseeds,
                private,
                author,
                trackers,
                add_to_session,
            ).addCallback(hide_progress)

        # Setup progress dialog
        self.builder.get_object('progress_dialog').set_transient_for(component.get('MainWindow').window)
        self.builder.get_object('progress_dialog').show_all()

        self.dialog.destroy()

    def create_torrent(
        self, path, tracker, piece_length, progress, comment, target,
        webseeds, private, created_by, trackers, add_to_session,
    ):
        import deluge.metafile
        deluge.metafile.make_meta_file(
            path,
            tracker,
            piece_length,
            progress=progress,
            comment=comment,
            target=target,
            webseeds=webseeds,
            private=private,
            created_by=created_by,
            trackers=trackers,
        )

        if add_to_session:
            with open(target, 'rb') as _file:
                filedump = b64encode(_file.read())
            client.core.add_torrent_file_async(
                os.path.split(target)[-1],
                filedump,
                {'download_location': os.path.split(path)[0]},
            )

    def _on_create_torrent_progress(self, value, num_pieces):
        percent = value / num_pieces

        def update_pbar_with_gobject(percent):
            pbar = self.builder.get_object('progressbar')
            pbar.set_text('%.2f%%' % (percent * 100))
            pbar.set_fraction(percent)
            return False

        if percent >= 0 and percent <= 1.0:
            # Make sure there are no threads race conditions that can
            # crash the UI while updating it.
            idle_add(update_pbar_with_gobject, percent)

    def on_button_up_clicked(self, widget):
        log.debug('on_button_up_clicked')
        row = self.builder.get_object('tracker_treeview').get_selection().get_selected()[1]
        if row is None:
            return
        if self.trackers_liststore[row][0] == 0:
            return
        else:
            self.trackers_liststore[row][0] -= 1

    def on_button_down_clicked(self, widget):
        log.debug('on_button_down_clicked')
        row = self.builder.get_object('tracker_treeview').get_selection().get_selected()[1]
        if row is None:
            return
        self.trackers_liststore[row][0] += 1

    def on_button_add_clicked(self, widget):
        log.debug('on_button_add_clicked')
        builder = Gtk.Builder()
        builder.add_from_file(resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'edit_trackers.add.ui'),
        ))
        dialog = builder.get_object('add_tracker_dialog')
        dialog.set_transient_for(self.dialog)
        textview = builder.get_object('textview_trackers')
        if self.config['createtorrent.trackers']:
            textview.get_buffer().set_text('\n'.join(self.config['createtorrent.trackers']))
        else:
            textview.get_buffer().set_text('')
        textview.grab_focus()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            # Create a list of trackers from the textview buffer
            textview_buf = textview.get_buffer()
            trackers_text = textview_buf.get_text(*textview_buf.get_bounds())
            log.debug('Create torrent tracker lines: %s', trackers_text)
            self.config['createtorrent.trackers'] = trackers_text.split('/n')

            # Append trackers liststore with unique trackers and tiers starting from last tier number.
            last_tier, orig_trackers = last_tier_trackers_from_liststore(self.trackers_liststore)
            for tracker, tier in trackers_tiers_from_text(trackers_text).items():
                if tracker not in orig_trackers:
                    self.trackers_liststore.append([tier + last_tier, tracker])

        dialog.destroy()

    def on_button_remove_clicked(self, widget):
        log.debug('on_button_remove_clicked')
        row = self.builder.get_object('tracker_treeview').get_selection().get_selected()[1]
        if row is None:
            return
        self.trackers_liststore.remove(row)
