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
from render import render, error_page
import page_decorators as deco
import lib.newforms_plus as forms
import web

class OptionsForm(forms.Form):
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
        data = proxy.get_config()
        log.debug("add:Init options with:%s" % data)
        return data

class AddForm(forms.Form):
    url = forms.CharField(label=_("Url"), required=False,
        widget=forms.TextInput(attrs={'size':60}))
    torrent = forms.CharField(label=_("Upload torrent"), required=False,
        widget=forms.FileInput(attrs={'size':60}))
    #hash = forms.CharField(label=_("Hash"), required=False,
    #    widget=forms.TextInput(attrs={'size':60}))
    #ret = forms.CheckBox(_('Add more'))

    #choose_files = forms.CheckBox(_('Choose Files')) #BROKEN!


class torrent_add:

    def add_page(self,error = None):
        vars  = web.input(url = None)
        form_data = {'url':vars.url}

        options_data = None
        if error:
            options_data = utils.get_newforms_data(OptionsForm)
            log.debug("add:(error-state):Init options with:%s" % options_data)
        return render.torrent_add(AddForm(form_data),OptionsForm(options_data), error)

    @deco.deluge_page
    def GET(self, name):
        return self.add_page()


    @deco.check_session
    def POST(self, name):
        """
        allows:
        *posting of url
        *posting file-upload
        """
        vars = web.input(url = None, torrent = {},choose_files = False)

        options_form = OptionsForm(utils.get_newforms_data(OptionsForm))
        if not options_form.is_valid():
            print self.add_page(error = _("Error in torrent options."))
            return
        options = options_form.cleaned_data



        torrent_name = None
        torrent_data  = None
        if vars.torrent.filename:
            torrent_name = vars.torrent.filename
            torrent_data  = vars.torrent.file.read()

        if vars.url and torrent_name:
            #error_page(_("Choose an url or a torrent, not both."))
            print self.add_page(error = _("Choose an url or a torrent, not both."))
            return

        if vars.url:
            proxy.add_torrent_url(vars.url,options)
            log.debug("add-url:options :%s" % options)
            self.redirect(vars.choose_files)
        elif torrent_name:
            proxy.add_torrent_file_binary(vars.torrent.filename, torrent_data, options)
            log.debug("add-file:options :%s" % options)
            self.redirect(vars.choose_files)
        else:
            print self.add_page(error = _("No data"))
            return

    def redirect(self,choose_files):
        if choose_files: #redirect to file chooser
            torrent_id = proxy.get_session_state()[-1] #HACK! no return-value for torrent_add_*
            utils.seeother("/torrent/files/%s" % torrent_id)

        else: #default
            utils.do_redirect()


def register():
    component.get("PageManager").register_page("/torrent/add(.*)",torrent_add)