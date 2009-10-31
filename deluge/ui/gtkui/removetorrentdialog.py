#
# removetorrentdialog.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
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

import gtk, gtk.glade
import pkg_resources

from deluge.ui.client import client
import deluge.component as component
from deluge.log import LOG as log

class RemoveTorrentDialog(object):
    """
    This class is used to create and show a Remove Torrent Dialog.

    :param torrent_ids: the torrent_ids to remove
    :type torrent_ids: list of torrent_ids

    :raises TypeError: if `torrent_id` is not a sequence type
    :raises ValueError: if `torrent_id` contains no torrent_ids or is None

    """
    def __init__(self, torrent_ids):
        if type(torrent_ids) != list and type(torrent_ids) != tuple:
            raise TypeError("requires a list of torrent_ids")

        if not torrent_ids:
            raise ValueError("requires a list of torrent_ids")

        self.__torrent_ids = torrent_ids

        glade = gtk.glade.XML(
            pkg_resources.resource_filename("deluge.ui.gtkui",
                "glade/remove_torrent_dialog.glade"))

        self.__dialog = glade.get_widget("remove_torrent_dialog")
        self.__dialog.set_transient_for(component.get("MainWindow").window)
        self.__dialog.set_title("")

        if len(self.__torrent_ids) > 1:
            # We need to pluralize the dialog
            label_title = glade.get_widget("label_title")
            button_ok = glade.get_widget("button_ok_label")
            button_data = glade.get_widget("button_data_label")

            def pluralize_torrents(text):
                plural_torrent = _("Torrents")
                return text.replace("torrent", plural_torrent.lower()).replace("Torrent", plural_torrent)

            label_title.set_markup(pluralize_torrents(label_title.get_label()))
            button_ok.set_label(pluralize_torrents(button_ok.get_label()))
            button_data.set_label(pluralize_torrents(button_data.get_label()))

    def __remove_torrents(self, remove_data):
        # Unselect all to avoid issues with the selection changed event
        component.get("TorrentView").treeview.get_selection().unselect_all()

        for torrent_id in self.__torrent_ids:
            client.core.remove_torrent(torrent_id, remove_data)

    def run(self):
        """
        Shows the dialog and awaits for user input.  The user can select to
        remove the torrent(s) from the session with or without their data.
        """
        # Response IDs from the buttons
        RESPONSE_SESSION = 1
        RESPONSE_DATA = 2

        response = self.__dialog.run()
        if response == RESPONSE_SESSION:
            self.__remove_torrents(False)
        elif response == RESPONSE_DATA:
            self.__remove_torrents(True)

        self.__dialog.destroy()
