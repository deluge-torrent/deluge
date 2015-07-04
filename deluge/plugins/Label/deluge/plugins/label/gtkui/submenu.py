# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


import logging

from deluge import component  # for systray
from deluge.ui.client import client
from gi.repository import Gtk

log = logging.getLogger(__name__)


# Deferred Translation
def _(message):
    return message
NO_LABEL = _("No Label")
del _


class LabelMenu(Gtk.MenuItem):
    def __init__(self):
        Gtk.MenuItem.__init__(self, _("Label"))

        self.sub_menu = Gtk.Menu()
        self.set_submenu(self.sub_menu)
        self.items = []

        # attach..
        component.get("MenuBar").torrentmenu
        self.sub_menu.connect("show", self.on_show, None)

    def get_torrent_ids(self):
        return component.get("TorrentView").get_selected_torrents()

    def on_show(self, widget=None, data=None):
        log.debug("label-on-show")
        client.label.get_labels().addCallback(self.cb_labels)

    def cb_labels(self, labels):
        for child in self.sub_menu.get_children():
            self.sub_menu.remove(child)
        for label in [NO_LABEL] + list(labels):
            if label == NO_LABEL:
                item = Gtk.MenuItem(_(NO_LABEL))
            else:
                item = Gtk.MenuItem(label.replace("_", "__"))
            item.connect("activate", self.on_select_label, label)
            self.sub_menu.append(item)
        self.show_all()

    def on_select_label(self, widget=None, label_id=None):
        log.debug("select label:%s,%s" % (label_id, self.get_torrent_ids()))
        for torrent_id in self.get_torrent_ids():
            client.label.set_torrent(torrent_id, label_id)
