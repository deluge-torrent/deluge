# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os

from gi.repository import Gtk

import deluge.common
import deluge.component as component
from deluge.ui.client import client

log = logging.getLogger(__name__)


class RemoveTorrentDialog(object):
    """
    This class is used to create and show a Remove Torrent Dialog.

    :param torrent_ids: the torrent_ids to remove
    :type torrent_ids: list of torrent_ids

    :raises TypeError: if `torrent_id` is not a sequence type
    :raises ValueError: if `torrent_id` contains no torrent_ids or is None

    """

    def __init__(self, torrent_ids, delete_files=False):
        if not isinstance(torrent_ids, list) and not isinstance(torrent_ids, tuple):
            raise TypeError('requires a list of torrent_ids')

        if not torrent_ids:
            raise ValueError('requires a list of torrent_ids')

        self.__torrent_ids = torrent_ids

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            deluge.common.resource_filename(
                __package__, os.path.join('glade', 'remove_torrent_dialog.ui')
            )
        )

        self.__dialog = self.builder.get_object('remove_torrent_dialog')
        self.__dialog.set_transient_for(component.get('MainWindow').window)

        self.builder.connect_signals(self)
        self.builder.get_object('delete_files').set_active(delete_files)
        label_title = self.builder.get_object('label_title')
        label_torrents = self.builder.get_object('label_torrents')
        num_torrents = len(self.__torrent_ids)
        if num_torrents == 1:
            label_torrents.set_markup(
                component.get('TorrentView').get_torrent_status(self.__torrent_ids[0])[
                    'name'
                ]
            )
        else:
            label_title.set_markup(_('Remove the selected torrents?'))
            label_torrents.set_markup(_('Total of %s torrents selected') % num_torrents)

    def on_delete_files_toggled(self, widget):
        self.builder.get_object('warning_label').set_visible(widget.get_active())

    def __remove_torrents(self, remove_data):
        # Unselect all to avoid issues with the selection changed event
        component.get('TorrentView').treeview.get_selection().unselect_all()

        def on_removed_finished(errors):
            if errors:
                log.info('Error(s) occured when trying to delete torrent(s).')
                for t_id, e_msg in errors:
                    log.warning('Error removing torrent %s : %s', t_id, e_msg)

        d = client.core.remove_torrents(self.__torrent_ids, remove_data)
        d.addCallback(on_removed_finished)

    def run(self):
        """
        Shows the dialog and awaits for user input.  The user can select to
        remove the torrent(s) from the session with or without their data.
        """
        if self.__dialog.run() == Gtk.ResponseType.OK:
            self.__remove_torrents(self.builder.get_object('delete_files').get_active())
        self.__dialog.destroy()
