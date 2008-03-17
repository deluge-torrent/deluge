#
# files_tab.py
#
# Copyright (C) 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
# 	Boston, MA    02110-1301, USA.
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

import gtk, gtk.glade
import gobject
import gettext
import os.path

from deluge.ui.client import aclient as client
import deluge.component as component
import deluge.common
import deluge.ui.gtkui.listview

from deluge.log import LOG as log

class FilesTab:
    def __init__(self):
        glade = component.get("MainWindow").get_glade()
        self.listview = glade.get_widget("files_listview")
        # country, filename, size, priority
        self.liststore = gtk.ListStore(str, gobject.TYPE_UINT64, str, int, str)
        
        # Filename column        
        column = gtk.TreeViewColumn(_("Filename"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, "text", 0)
        self.listview.append_column(column)

        # Size column        
        column = gtk.TreeViewColumn(_("Size"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.set_cell_data_func(render, deluge.ui.gtkui.listview.cell_data_size, 1)
        self.listview.append_column(column)

        # Progress column        
        column = gtk.TreeViewColumn(_("Progress"))
        render = gtk.CellRendererProgress()
        column.pack_start(render, False)
        column.add_attribute(render, "text", 2)
        column.add_attribute(render, "value", 3)
        self.listview.append_column(column)
        
        # Priority column        
        column = gtk.TreeViewColumn(_("Priority"))
        render = gtk.CellRendererText()
        column.pack_start(render, False)
        column.add_attribute(render, "text", 4)
        self.listview.append_column(column)

        self.listview.set_model(self.liststore)
        
        # torrent_id: (filepath, size)
        self.files_list = {}
        
        self.torrent_id = None
        
    def update(self):
        # Get the first selected torrent
        torrent_id = component.get("TorrentView").get_selected_torrents()

        # Only use the first torrent in the list or return if None selected
        if len(torrent_id) != 0:
            torrent_id = torrent_id[0]
        else:
            # No torrent is selected in the torrentview
            self.liststore.clear()
            return
        
        if torrent_id != self.torrent_id:
            # We only want to do this if the torrent_id has changed
            self.liststore.clear()
            self.torrent_id = torrent_id
            
            if self.torrent_id not in self.files_list.keys():
                # We need to get the files list
                log.debug("Getting file list from core..")
                client.get_torrent_status(
                    self._on_get_torrent_files, 
                    self.torrent_id, 
                    ["files", "file_progress", "file_priorities"])
                client.force_call(block=True)
            else:
                self.update_files()
                client.get_torrent_status(self._on_get_torrent_status, self.torrent_id, ["file_progress", "file_priorities"])
                client.force_call(True)
        else:
            client.get_torrent_status(self._on_get_torrent_status, self.torrent_id, ["file_progress", "file_priorities"])
            client.force_call(True)
        
    def update_files(self):
        # Updates the filename and size columns based on info in self.files_list
        # This assumes the list is currently empty.
        for file in self.files_list[self.torrent_id]:
            row = self.liststore.append()
            # Store the torrent id
            self.liststore.set_value(row, 0, 
                    os.path.split(file["path"])[1])
            self.liststore.set_value(row, 1, file["size"])
        
    def _on_get_torrent_files(self, status):
        self.files_list[self.torrent_id] = status["files"]
        self.update_files()
        self._on_get_torrent_status(status)
        
    def _on_get_torrent_status(self, status):
        for index, row in enumerate(self.liststore):
            row[2] = "%.2f%%" % (status["file_progress"][index] * 100)
            row[3] = status["file_progress"][index] * 100
            row[4] = status["file_priorities"][index]
           
    def clear(self):
        self.liststore.clear()
