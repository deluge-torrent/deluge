# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.ui.client import client


class NewReleaseDialog:
    def __init__(self):
        pass

    def show(self, available_version):
        self.config = ConfigManager("gtkui.conf")
        builder = component.get("MainWindow").get_builder()
        self.dialog = builder.get_object("new_release_dialog")
        # Set the version labels
        if deluge.common.windows_check() or deluge.common.osx_check():
            builder.get_object("image_new_release").set_from_file(
                deluge.common.get_pixmap("deluge16.png"))
        else:
            builder.get_object("image_new_release").set_from_icon_name("deluge", 4)
        builder.get_object("label_available_version").set_text(available_version)
        builder.get_object("label_client_version").set_text(
            deluge.common.get_version())
        self.chk_not_show_dialog = builder.get_object("chk_do_not_show_new_release")
        builder.get_object("button_goto_downloads").connect(
            "clicked", self._on_button_goto_downloads)
        builder.get_object("button_close_new_release").connect(
            "clicked", self._on_button_close_new_release)

        if client.connected():
            def on_info(version):
                builder.get_object("label_server_version").set_text(version)
                builder.get_object("label_server_version").show()
                builder.get_object("label_server_version_text").show()

            if not client.is_classicmode():
                builder.get_object("label_client_version_text").set_label(_("<i>Client Version</i>"))
                client.daemon.info().addCallback(on_info)

        self.dialog.show()

    def _on_button_goto_downloads(self, widget):
        deluge.common.open_url_in_browser("http://deluge-torrent.org")
        self.config["show_new_releases"] = not self.chk_not_show_dialog.get_active()
        self.dialog.destroy()

    def _on_button_close_new_release(self, widget):
        self.config["show_new_releases"] = not self.chk_not_show_dialog.get_active()
        self.dialog.destroy()
