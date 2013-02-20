#
# createtorrentdialog.py
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
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


import gtk
import sys
import pkg_resources
import os.path
import gobject
import base64

from twisted.internet.threads import deferToThread

from deluge.ui.client import client
import listview
import deluge.component as component
import deluge.common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class CreateTorrentDialog:
    def show(self):
        self.glade = gtk.glade.XML(
            pkg_resources.resource_filename(
                "deluge.ui.gtkui",
                "glade/create_torrent_dialog.glade"))

        self.config = ConfigManager("gtkui.conf")

        self.dialog = self.glade.get_widget("create_torrent_dialog")
        self.dialog.set_transient_for(component.get("MainWindow").window)

        self.glade.signal_autoconnect({
            "on_button_file_clicked": self._on_button_file_clicked,
            "on_button_folder_clicked": self._on_button_folder_clicked,
            "on_button_remote_path_clicked": self._on_button_remote_path_clicked,
            "on_button_cancel_clicked": self._on_button_cancel_clicked,
            "on_button_save_clicked": self._on_button_save_clicked,
            "on_button_up_clicked": self._on_button_up_clicked,
            "on_button_add_clicked": self._on_button_add_clicked,
            "on_button_remove_clicked": self._on_button_remove_clicked,
            "on_button_down_clicked": self._on_button_down_clicked
        })

        # path, icon, size
        self.files_treestore = gtk.TreeStore(str, str, gobject.TYPE_UINT64)

        column = gtk.TreeViewColumn(_("Filename"))
        render = gtk.CellRendererPixbuf()
        column.pack_start(render, False)
        column.add_attribute(render, "stock-id", 1)
        render = gtk.CellRendererText()
        column.pack_start(render, True)
        column.add_attribute(render, "text", 0)
        column.set_expand(True)
        self.glade.get_widget("treeview_files").append_column(column)

        column = gtk.TreeViewColumn(_("Size"))
        render = gtk.CellRendererText()
        column.pack_start(render)
        column.set_cell_data_func(render, listview.cell_data_size, 2)
        self.glade.get_widget("treeview_files").append_column(column)

        self.glade.get_widget("treeview_files").set_model(self.files_treestore)
        self.glade.get_widget("treeview_files").set_show_expanders(False)

        # tier, url
        self.trackers_liststore = gtk.ListStore(int, str)

        self.glade.get_widget("tracker_treeview").append_column(
            gtk.TreeViewColumn(_("Tier"), gtk.CellRendererText(), text=0))
        self.glade.get_widget("tracker_treeview").append_column(
            gtk.TreeViewColumn(_("Tracker"), gtk.CellRendererText(), text=1))

        self.glade.get_widget("tracker_treeview").set_model(self.trackers_liststore)
        self.trackers_liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)

        if not client.is_localhost() and client.connected():
            self.glade.get_widget("button_remote_path").show()
        else:
            self.glade.get_widget("button_remote_path").hide()

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
        model = self.glade.get_widget("combo_piece_size").get_model()
        for index,value in enumerate(model):
            psize = self.parse_piece_size_text(value[0])
            pieces = size / psize
            if pieces < 2048 or (index + 1) == len(model):
                self.glade.get_widget("combo_piece_size").set_active(index)
                break

    def _on_button_file_clicked(self, widget):
        log.debug("_on_button_file_clicked")
        # Setup the filechooserdialog
        chooser = gtk.FileChooserDialog(_("Choose a file"),
            self.dialog,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN,
                        gtk.RESPONSE_OK))

        chooser.set_transient_for(self.dialog)
        chooser.set_select_multiple(False)
        chooser.set_property("skip-taskbar-hint", True)

        # Run the dialog
        response = chooser.run()

        if response == gtk.RESPONSE_OK:
            result = chooser.get_filename()
        else:
            chooser.destroy()
            return

        path = result.decode('utf-8')

        self.files_treestore.clear()
        self.files_treestore.append(None, [result, gtk.STOCK_FILE, deluge.common.get_path_size(path)])
        self.adjust_piece_size()
        chooser.destroy()

    def _on_button_folder_clicked(self, widget):
        log.debug("_on_button_folder_clicked")
        # Setup the filechooserdialog
        chooser = gtk.FileChooserDialog(_("Choose a folder"),
            self.dialog,
            gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN,
                        gtk.RESPONSE_OK))

        chooser.set_transient_for(self.dialog)
        chooser.set_select_multiple(False)
        chooser.set_property("skip-taskbar-hint", True)
        # Run the dialog
        response = chooser.run()

        if response == gtk.RESPONSE_OK:
            result = chooser.get_filename()
        else:
            chooser.destroy()
            return

        path = result.decode('utf-8')

        self.files_treestore.clear()
        self.files_treestore.append(None, [result, gtk.STOCK_OPEN, deluge.common.get_path_size(path)])
        self.adjust_piece_size()
        chooser.destroy()

    def _on_button_remote_path_clicked(self, widget):
        log.debug("_on_button_remote_path_clicked")
        dialog = self.glade.get_widget("remote_path_dialog")
        entry = self.glade.get_widget("entry_path")
        dialog.set_transient_for(self.dialog)
        entry.set_text("/")
        entry.grab_focus()
        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            result = entry.get_text()
            def _on_get_path_size(size):
                log.debug("size: %s", size)
                if size > 0:
                    self.files_treestore.clear()
                    self.files_treestore.append(None, [result, gtk.STOCK_NETWORK, size])
                    self.adjust_piece_size()
            client.core.get_path_size(result).addCallback(_on_get_path_size)
            client.force_call(True)

        dialog.hide()

    def _on_button_cancel_clicked(self, widget):
        log.debug("_on_button_cancel_clicked")
        self.dialog.destroy()

    def _on_button_save_clicked(self, widget):
        log.debug("_on_button_save_clicked")
        if len(self.files_treestore) == 0:
            return

        is_remote = self.files_treestore[0][1] == gtk.STOCK_NETWORK
        if is_remote:
            # This is a remote path
            dialog = self.glade.get_widget("remote_save_dialog")
            dialog_save_path = self.glade.get_widget("entry_save_path")
            dialog_save_path.set_text(self.files_treestore[0][0].rstrip("\\/") + ".torrent")
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                result = dialog_save_path.get_text()
            else:
                dialog.hide()
                return
            dialog.hide()
        else:
            # Setup the filechooserdialog
            chooser = gtk.FileChooserDialog(_("Save .torrent file"),
                self.dialog,
                gtk.FILE_CHOOSER_ACTION_SAVE,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE,
                            gtk.RESPONSE_OK))

            chooser.set_transient_for(self.dialog)
            chooser.set_select_multiple(False)
            chooser.set_property("skip-taskbar-hint", True)

            # Add .torrent and * file filters
            file_filter = gtk.FileFilter()
            file_filter.set_name(_("Torrent files"))
            file_filter.add_pattern("*." + "torrent")
            chooser.add_filter(file_filter)
            file_filter = gtk.FileFilter()
            file_filter.set_name(_("All files"))
            file_filter.add_pattern("*")
            chooser.add_filter(file_filter)

            chooser.set_current_name(os.path.split(self.files_treestore[0][0])[-1] + ".torrent")
            # Run the dialog
            response = chooser.run()

            if response == gtk.RESPONSE_OK:
                result = chooser.get_filename()
            else:
                chooser.destroy()
                return
            chooser.destroy()

        # Fix up torrent filename
        if len(result) < 9:
            result += ".torrent"
        elif result[-8:] != ".torrent":
            result += ".torrent"

        # Get the path
        path = self.files_treestore[0][0]
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
        webseeds = []
        b = self.glade.get_widget("textview_webseeds").get_buffer()
        lines = b.get_text(b.get_start_iter(), b.get_end_iter()).strip().split("\n")
        import deluge.common
        for l in lines:
            if deluge.common.is_url(l):
                webseeds.append(l)
        # Get the piece length in bytes
        combo = self.glade.get_widget("combo_piece_size")
        piece_length = \
            self.parse_piece_size_text(combo.get_model()[combo.get_active()][0])
        num_pieces = self.files_treestore[0][2] / piece_length

        author = self.glade.get_widget("entry_author").get_text()
        comment = self.glade.get_widget("entry_comments").get_text()
        private = self.glade.get_widget("chk_private_flag").get_active()
        add_to_session = self.glade.get_widget("chk_add_to_session").get_active()

        if is_remote:
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
                add_to_session)

        else:
            # Setup progress dialog
            self.glade.get_widget("progress_dialog").set_transient_for(component.get("MainWindow").window)
            self.glade.get_widget("progress_dialog").show_all()

            def hide_progress(result):
                self.glade.get_widget("progress_dialog").hide_all()

            deferToThread(self.create_torrent,
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
                    add_to_session).addCallback(hide_progress)

        self.dialog.destroy()

    def create_torrent(self, path, tracker, piece_length, progress, comment, target,
                        webseeds, private, created_by, trackers, add_to_session):
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
            trackers=trackers)

        if add_to_session:
            client.core.add_torrent_file(
                os.path.split(target)[-1],
                base64.encodestring(open(target, "rb").read()),
                {"download_location": os.path.split(path)[0]})

    def _on_create_torrent_progress(self, value, num_pieces):
        percent = float(value)/float(num_pieces)
        pbar = self.glade.get_widget("progressbar")
        pbar.set_text("%.2f%%" % (percent*100))
        if percent >= 0 and percent <= 1.0:
            pbar.set_fraction(percent)

    def _on_button_up_clicked(self, widget):
        log.debug("_on_button_up_clicked")
        row = self.glade.get_widget("tracker_treeview").get_selection().get_selected()[1]
        if row is None:
            return
        if self.trackers_liststore[row][0] == 0:
            return
        else:
            self.trackers_liststore[row][0] -= 1

    def _on_button_down_clicked(self, widget):
        log.debug("_on_button_down_clicked")
        row = self.glade.get_widget("tracker_treeview").get_selection().get_selected()[1]
        if row is None:
            return
        self.trackers_liststore[row][0] += 1

    def _on_button_add_clicked(self, widget):
        log.debug("_on_button_add_clicked")
        glade = gtk.glade.XML(
            pkg_resources.resource_filename(
                "deluge.ui.gtkui",
                "glade/edit_trackers.glade"))
        dialog = glade.get_widget("add_tracker_dialog")
        dialog.set_transient_for(self.dialog)
        textview = glade.get_widget("textview_trackers")
        if self.config["createtorrent.trackers"]:
            textview.get_buffer().set_text("\n".join(self.config["createtorrent.trackers"]))
        else:
            textview.get_buffer().set_text("")
        textview.grab_focus()
        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            # Create a list of trackers from the textview buffer
            trackers = []
            b = textview.get_buffer()
            lines = b.get_text(b.get_start_iter(), b.get_end_iter()).strip().split("\n")
            self.config["createtorrent.trackers"] = lines
            log.debug("lines: %s", lines)
            for l in lines:
                if deluge.common.is_url(l):
                    trackers.append(l)

            # We are going to add these trackers to the heighest tier + 1
            tier = 0
            for row in self.trackers_liststore:
                if row[0] > tier:
                    tier = row[0]

            for tracker in trackers:
                self.trackers_liststore.append([tier, tracker])

        dialog.destroy()

    def _on_button_remove_clicked(self, widget):
        log.debug("_on_button_remove_clicked")
        row = self.glade.get_widget("tracker_treeview").get_selection().get_selected()[1]
        if row is None:
            return
        self.trackers_liststore.remove(row)
