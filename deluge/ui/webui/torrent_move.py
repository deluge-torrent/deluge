#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
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

#

from deluge.ui.client import sclient as proxy
from deluge.log import LOG as log
from deluge import component

import utils
from render import render
import page_decorators as deco
import lib.newforms_plus as forms

#Too much boilerplate code here, todo : fix it.

class MoveForm(forms.Form):
    save_path = forms.ServerFolder(_("Move To"))
    def initial_data(self):
        return {'save_path':proxy.get_config_value('download_location')}

class torrent_move:

    def move_page(self, name, error = None):
        torrent_ids = name.split(',')
        torrent_list = [utils.get_torrent_status(id) for id in torrent_ids]

        data = None
        if error:
            data = utils.get_newforms_data(MoveForm)

        form = MoveForm(data)

        return render.torrent_move(name, torrent_list , form, error)

    @deco.deluge_page
    def GET(self, name):
        return self.move_page(name)

    @deco.check_session
    def POST(self, name):
        torrent_ids = name.split(',')
        form = MoveForm(utils.get_newforms_data(MoveForm))
        if not form.is_valid():
            print self.move_page(name, error = _("Error in Path."))
            return
        save_path = form.cleaned_data["save_path"]
        proxy.move_storage(torrent_ids, save_path)
        utils.do_redirect()

def register():
    component.get("PageManager").register_page("/torrent/move/(.*)",torrent_move)
