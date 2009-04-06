#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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

from deluge.ui.client import sclient, aclient
from deluge.log import LOG as log
from deluge import component

import page_decorators as deco
import lib.newforms_plus as forms
from render import error_page
import utils

class TorrentOptionsForm(forms.Form):
    #download
    max_download_speed = forms.DelugeFloat(
        _("Maximum Down Speed"))
    max_upload_speed = forms.DelugeFloat(
        _("Maximum Up Speed"))
    max_connections =  forms.DelugeInt(_("Maximum Connections"))
    max_upload_slots = forms.DelugeInt(_("Maximum Upload Slots"))

    #general
    prioritize_first_last = forms.CheckBox(_('Prioritize First/Last'))

    #Ratio
    is_auto_managed =  forms.CheckBox(_('Auto Managed'))
    stop_at_ratio =  forms.CheckBox(_('Stop seed at ratio'))
    stop_ratio = forms.FloatField(min_value=-1)
    remove_at_ratio = forms.CheckBox(_('Remove at ratio'))


class torrent_options:
    @deco.check_session
    @deco.torrent
    def POST(self, torrent):
        options_form = TorrentOptionsForm(utils.get_newforms_data(TorrentOptionsForm))
        if not options_form.is_valid():
            #!!!!!!!!!!!!!
            #todo:user-friendly error-handling.
            #!!!!!!!!
            return error_page(_("Error in torrent options."))
        options = options_form.cleaned_data


        #options['prioritize_first_last']
        aclient.set_torrent_max_connections(torrent.id, options['max_connections'])
        aclient.set_torrent_max_download_speed(torrent.id, options['max_download_speed'])
        aclient.set_torrent_max_upload_slots(torrent.id, options['max_upload_slots'])
        aclient.set_torrent_max_upload_speed(torrent.id, options['max_upload_speed'])

        aclient.set_torrent_prioritize_first_last(torrent.id, options['prioritize_first_last'])
        aclient.set_torrent_auto_managed(torrent.id, options['is_auto_managed'])
        aclient.set_torrent_stop_at_ratio(torrent.id, options['stop_at_ratio'])
        aclient.set_torrent_stop_ratio(torrent.id, options['stop_ratio'])
        aclient.set_torrent_remove_at_ratio(torrent.id, options['remove_at_ratio'])


        aclient.force_call()

        utils.do_redirect()




def register():
    from render import template
    template.Template.globals["forms"].torrent_options = lambda torrent : TorrentOptionsForm(torrent)
    component.get("PageManager").register_page("/torrent/options/(.*)", torrent_options)
