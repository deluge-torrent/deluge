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
#
from webserver_common import ws
import utils
from render import template
import page_decorators as deco
import lib.newforms_plus as forms
import lib.webpy022 as web

class TorrentOptionsForm(forms.Form):

#download
    max_download_speed = forms.DelugeFloat(
        _("Maximum Down Speed"))
    max_upload_speed = forms.DelugeFloat(
        _("Maximum Up Speed"))
    max_connections =  forms.DelugeInt(_("Maximum Connections"))
    max_upload_slots = forms.DelugeInt(_("Maximum Upload Slots"))
    #general
    prioritize_first_last = forms.CheckBox(
        _('Prioritize first and last pieces'))
    private = forms.CheckBox(_('Private'))

template.Template.globals["forms"].torrent_options = lambda torrent : TorrentOptionsForm(torrent)

