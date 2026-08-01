#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


import logging

from gi.repository.Gtk import CheckMenuItem, Menu, MenuItem

from deluge import component  # for systray
from deluge.ui.client import client

log = logging.getLogger(__name__)


# Deferred Translation
def _(message):
    return message


NO_LABEL = _('No Label')
del _


class LabelMenu(MenuItem):
    def __init__(self):
        MenuItem.__init__(self, _('Label'))  # noqa: F821

        self.sub_menu = Menu()
        self.set_submenu(self.sub_menu)
        self.items = []

        # attach..
        self.sub_menu.connect('show', self.on_show, None)

    def get_torrent_ids(self):
        return component.get('TorrentView').get_selected_torrents()

    def on_show(self, widget=None, data=None):
        log.debug('label-on-show')
        client.label.get_labels().addCallback(self.cb_labels)

    def cb_labels(self, labels):
        for child in self.sub_menu.get_children():
            self.sub_menu.remove(child)
        self.items = []
        item = MenuItem(_(NO_LABEL))  # noqa: F821
        item.connect('activate', self.on_select_label, NO_LABEL)
        self.sub_menu.append(item)
        for label in list(labels):
            item = CheckMenuItem(label)
            item.connect('toggled', self.on_toggle_label, label)
            self.sub_menu.append(item)
            self.items.append(item)

        self.update_check_state()
        self.show_all()

    def update_check_state(self):
        torrent_ids = self.get_torrent_ids()
        if not torrent_ids or not self.items:
            return
        client.core.get_torrents_status({'id': torrent_ids}, ['label']).addCallback(
            self.cb_status, torrent_ids
        )

    def cb_status(self, statuses, torrent_ids):
        self.updating = True
        for item in self.items:
            label = item.get_label()
            active = True
            for torrent_id in torrent_ids:
                labels = statuses.get(torrent_id, {}).get('label') or []
                if isinstance(labels, str):
                    labels = labels.split(', ')
                if label not in labels:
                    active = False
                    break
            item.set_active(active)
        self.updating = False

    def on_toggle_label(self, widget=None, label_id=None):
        if getattr(self, 'updating', False):
            return
        log.debug('toggle label:%s,%s', label_id, self.get_torrent_ids())
        if widget.get_active():
            for torrent_id in self.get_torrent_ids():
                client.label.add_label(torrent_id, label_id)
        else:
            for torrent_id in self.get_torrent_ids():
                client.label.remove_label(torrent_id, label_id)

    def on_select_label(self, widget=None, label_id=None):
        log.debug('select label:%s,%s', label_id, self.get_torrent_ids())
        for torrent_id in self.get_torrent_ids():
            client.label.set_torrent(torrent_id, label_id)
