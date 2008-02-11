#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

from webserver_common import ws
from utils import *
from render import render, error_page
import page_decorators as deco
import lib.newforms_plus as forms

"""
        self.glade.get_widget("button_location").set_current_folder(
            options["download_location"])
        self.glade.get_widget("radio_compact").set_active(
            options["compact_allocation"])
        self.glade.get_widget("spin_maxdown").set_value(
            options["max_download_speed_per_torrent"])
        self.glade.get_widget("spin_maxup").set_value(
            options["max_upload_speed_per_torrent"])
        self.glade.get_widget("spin_maxconnections").set_value(
            options["max_connections_per_torrent"])
        self.glade.get_widget("spin_maxupslots").set_value(
            options["max_upload_slots_per_torrent"])
        self.glade.get_widget("chk_paused").set_active(
            options["add_paused"])
        self.glade.get_widget("chk_prioritize").set_active(
            options["prioritize_first_last_pieces"])
        self.glade.get_widget("chk_private").set_active(
            options["default_private"])
"""
class AddForm(forms.Form):
    download_location =  forms.ServerFolder(_("Download Location"))
    compact_allocation = forms.CheckBox(_("Compact Allocation"))

    #download
    max_download_speed_per_torrent = forms.DelugeFloat(
        _("Maximum Down Speed"))
    max_upload_speed_per_torrent = forms.DelugeFloat(
        _("Maximum Up Speed"))
    max_connections_per_torrent = forms.DelugeInt(_("Maximum Connections"))
    max_upload_slots_per_torrent = forms.DelugeInt(_("Maximum Upload Slots"))
    #general
    prioritize_first_last_pieces = forms.CheckBox(
        _('Prioritize first and last pieces'))
    add_paused = forms.CheckBox(_('Add In Paused State'))
    default_private = forms.CheckBox(_('Set Private Flag'))

    def initial_data(self):
        return ws.proxy.get_config()

class torrent_add:

    @deco.deluge_page
    def GET(self, name):
        return render.torrent_add(AddForm())

    @deco.check_session
    def POST(self, name):
        """
        allows:
        *posting of url
        *posting file-upload
        *posting of data as string(for greasemonkey-private)
        """

        vars = web.input(url = None, torrent = {})

        torrent_name = None
        torrent_data  = None
        if vars.torrent.filename:
            torrent_name = vars.torrent.filename
            torrent_data  = vars.torrent.file.read()

        if vars.url and torrent_name:
            error_page(_("Choose an url or a torrent, not both."))
        if vars.url:
            ws.proxy.add_torrent_url(vars.url)
            do_redirect()
        elif torrent_name:
            data_b64 = base64.b64encode(torrent_data)
            #b64 because of strange bug-reports related to binary data
            ws.proxy.add_torrent_filecontent(vars.torrent.filename, data_b64)
            do_redirect()
        else:
            error_page(_("no data."))
