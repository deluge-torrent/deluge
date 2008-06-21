# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
# License: GPL v2(+OpenSSL exception), see LICENSE file in base directory.

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
    prioritize_first_last = forms.CheckBox(
        _('Prioritize first and last pieces [TODO!]'))
    #private = forms.CheckBox(_('Private'))

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
        aclient.set_torrent_private_flag(torrent.id,  options['private'])

        aclient.force_call()

        utils.do_redirect()




def register():
    from render import template
    template.Template.globals["forms"].torrent_options = lambda torrent : TorrentOptionsForm(torrent)
    component.get("PageManager").register_page("/torrent/options/(.*)", torrent_options)
