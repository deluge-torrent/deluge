#
# new_release_dialog.py
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


import deluge.component as component
import deluge.common
from deluge.configmanager import ConfigManager
from deluge.ui.client import client

class NewReleaseDialog:
    def __init__(self):
        pass

    def show(self, available_version):
        self.config = ConfigManager("gtkui.conf")
        glade = component.get("MainWindow").main_glade
        self.dialog = glade.get_widget("new_release_dialog")
        # Set the version labels
        if deluge.common.windows_check() or deluge.common.osx_check():
            glade.get_widget("image_new_release").set_from_file(
                deluge.common.get_pixmap("deluge16.png"))
        else:
            glade.get_widget("image_new_release").set_from_icon_name("deluge", 4)
        glade.get_widget("label_available_version").set_text(available_version)
        glade.get_widget("label_client_version").set_text(
            deluge.common.get_version())
        self.chk_not_show_dialog = glade.get_widget("chk_do_not_show_new_release")
        glade.get_widget("button_goto_downloads").connect(
            "clicked", self._on_button_goto_downloads)
        glade.get_widget("button_close_new_release").connect(
            "clicked", self._on_button_close_new_release)
        
        if client.connected():
            def on_info(version):
                glade.get_widget("label_server_version").set_text(version)
                glade.get_widget("label_server_version").show()
                glade.get_widget("label_server_version_text").show()

            if not client.is_classicmode():
                glade.get_widget("label_client_version_text").set_label(_("<i>Client Version</i>"))
                client.daemon.info().addCallback(on_info)

        self.dialog.show()

    def _on_button_goto_downloads(self, widget):
        deluge.common.open_url_in_browser("http://deluge-torrent.org")
        self.config["show_new_releases"] = not self.chk_not_show_dialog.get_active()
        self.dialog.destroy()

    def _on_button_close_new_release(self, widget):
        self.config["show_new_releases"] = not self.chk_not_show_dialog.get_active()
        self.dialog.destroy()

