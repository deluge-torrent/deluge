# -*- coding: utf-8 -*-
#
# deluge_webserver.py
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

import utils
from webserver_common import ws, proxy , log
import lib.newforms_plus as forms
import config_forms
from deluge import component

config_page = component.get("ConfigPageManager")

class NetworkPorts(config_forms.CfgForm ):
    title = _("Ports")
    info = _("Restart daemon after changing these values.")
    _port_from =  forms.IntegerField(_("From"))
    _port_to = forms.IntegerField(_("To"))
    random_port = forms.CheckBox(_("Random"))

    def initial_data(self):
        data = config_forms.CfgForm.initial_data(self)
        data['_port_from'] , data['_port_to'] = data['listen_ports']
        return data

    def save(self,data):
        data['listen_ports'] = [data['_port_from'] , data['_port_to'] ]
        del(data['_port_from'])
        del(data['_port_to'])
        config_forms.config.CfgForm.save(self, data)

    def validate(self, data):
        if (data['_port_to'] < data['_port_from']):
            raise ValidationError('"Port from" must be greater than "Port to"')

config_page.register('network','ports', NetworkPorts)

class NetworkExtra(config_forms.CfgForm ):
    title = _("Extra's")
    dht = forms.CheckBox(_("Mainline DHT"))
    upnp = forms.CheckBox(_("UpNP"))
    natpmp = forms.CheckBox(_("NAT-PMP"))
    utpex = forms.CheckBox(_("Peer-Exchange"))
    lsd = forms.CheckBox(_("LSD"))

config_page.register('network','extra', NetworkExtra)

class NetworkEnc(config_forms.CfgForm ):
    title = _("Encryption")

    _enc_choices = list(enumerate([_("Forced"),_("Enabled"),_("Disabled")]))
    _level_choices = list(enumerate([_("Handshake"), _("Full") , _("Either")]))

    enc_in_policy = forms.IntChoiceField(_("Inbound"), _enc_choices)
    enc_out_policy = forms.IntChoiceField(_("Outbound"), _enc_choices)
    enc_level = forms.IntChoiceField(_("Level"), _level_choices)
    enc_prefer_rc4 =  forms.CheckBox("Prefer to encrypt entire stream")

config_page.register('network','encryption', NetworkEnc)


class BandwithGlobal(config_forms.CfgForm):
    title = _("Global")
    info = _("-1 = Unlimited")
    max_connections_global = forms.DelugeInt(_("Maximum Connections"))
    max_download_speed = forms.DelugeFloat(_("Maximum Download Speed (Kib/s)"))
    max_upload_speed = forms.DelugeFloat(_("Maximum Upload Speed (Kib/s)"))
    max_upload_slots_global = forms.DelugeInt(_("Maximum Upload Slots"))

config_page.register('bandwidth','global', BandwithGlobal)

class BandwithTorrent(config_forms.CfgForm):
    title = _("Per Torrent")
    info = _("-1 = Unlimited")
    max_connections_per_torrent = forms.DelugeInt(_("Maximum Connections"))
    max_upload_slots_per_torrent = forms.DelugeInt(_("Maximum Upload Slots"))

config_page.register('bandwidth','torrent', BandwithTorrent)

class Download(config_forms.CfgForm):
    title = _("Download")
    download_location = forms.ServerFolder(_("Store all downoads in"))
    torrentfiles_location = forms.ServerFolder(_("Save .torrent files to"))
    autoadd_location = forms.ServerFolder(_("Auto Add folder"), required=False)
    compact_allocation = forms.CheckBox(_('Use Compact Allocation'))
    prioritize_first_last_pieces = forms.CheckBox(
        _('Prioritize first and last pieces'))

config_page.register('deluge','download', Download)

class Daemon(config_forms.CfgForm):
    title = _("Daemon")
    info = _("Restart daemon and webui after changing these settings")
    daemon_port     = forms.IntegerField(_("Port"))
    allow_remote = forms.CheckBox(_("Allow Remote Connections"))

config_page.register('deluge','daemon', Daemon)

class Plugins(forms.Form):
    title = _("Enabled Plugins")
    try:
        _choices = [(p,p) for p in proxy.get_available_plugins()]
        enabled_plugins = forms.MultipleChoice(_(""), _choices)
    except:
        log.error("Not connected to daemon, Unable to load plugin-list")
        #TODO: reload on reconnect!


    def initial_data(self):
        return {'enabled_plugins':proxy.get_enabled_plugins()}

    def save(self, value):
        raise forms.ValidationError("SAVE:TODO")

config_page.register('deluge','plugins', Plugins)

"""
class Queue(forms.Form):
    title = _("Queue")
    info = _("queue-cfg not finished")

    queue_top = forms.CheckBox(_("Queue new torrents to top"))
    total_active = forms.DelugeInt(_("Total active torrents"))
    total_seeding = forms.DelugeInt(_("Total active seeding"))
    total_downloading = forms.DelugeInt(_("Total active downloading"))

    queue_bottom = forms.CheckBox(_("Queue completed torrents to bottom"))
    stop_on_ratio = forms.CheckBox(_("Stop seeding when ratio reaches"))
    stop_ratio = forms.DelugeInt(_("TODO:float-edit-box"))
    remove_after_stop = forms.CheckBox(_("Remve torrent when ratio reached"))

    def save(self, value):
        raise forms.ValidationError("SAVE:TODO")

config_page.register('plugins','queue', Queue)
"""