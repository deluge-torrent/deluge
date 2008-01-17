#!/usr/bin/env python
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

import lib.newforms as forms
import config
import utils
from webserver_common import ws


class NetworkPorts(config.CfgForm ):
    title = _("Ports")
    info = _("Restart daemon after changing these values.")
    _port_from =  forms.IntegerField(_("From"))
    _port_to = forms.IntegerField(_("To"))
    random_port = config.CheckBox(_("Random"))

    def initial_data(self):
        data = config.CfgForm.initial_data(self)
        data['_port_from'] , data['_port_to'] = data['listen_ports']
        return data

    def save(self,data):
        data['listen_ports'] = [data['_port_from'] , data['_port_to'] ]
        del(data['_port_from'])
        del(data['_port_to'])
        config.CfgForm.save(self, data)

    def validate(self, data):
        if (data['_port_to'] < data['_port_from']):
            raise ValidationError('"Port from" must be greater than "Port to"')

config.register_block('network','ports', NetworkPorts)

class NetworkExtra(config.CfgForm ):
    title = _("Extra's")
    dht = config.CheckBox(_("Mainline DHT"))
    upnp = config.CheckBox(_("UpNP"))
    natpmp = config.CheckBox(_("NAT-PMP"))
    utpex = config.CheckBox(_("Peer-Exchange"))
    lsd = config.CheckBox(_("LSD"))

config.register_block('network','extra', NetworkExtra)

class NetworkEnc(config.CfgForm ):
    title = _("Encryption")

    _enc_choices = [_("Forced"),_("Enabled"),_("Disabled")]
    _level_choices = [_("Handshake"), _("Full") , _("Either")]

    enc_in_policy = config.IntCombo(_("Inbound"), _enc_choices)
    enc_out_policy = config.IntCombo(_("Outbound"), _enc_choices)
    enc_level = config.IntCombo(_("Level"), _level_choices)
    enc_prefer_rc4 =  config.CheckBox("Prefer to encrypt entire stream")

config.register_block('network','encryption', NetworkEnc)


class BandwithGlobal(config.CfgForm):
    title = _("Global")
    info = _("-1 = Unlimited")
    max_connections_global = config.DelugeInt(_("Maximum Connections"))
    max_download_speed = config.DelugeFloat(_("Maximum Download Speed (Kib/s)"))
    max_upload_speed = config.DelugeFloat(_("Maximum Upload Speed (Kib/s)"))
    max_upload_slots_global = config.DelugeInt(_("Maximum Upload Slots"))

config.register_block('bandwidth','global', BandwithGlobal)

class BandwithTorrent(config.CfgForm):
    title = _("Per Torrent")
    info = _("-1 = Unlimited")
    max_connections_per_torrent = config.DelugeInt(_("Maximum Connections"))
    max_upload_slots_per_torrent = config.DelugeInt(_("Maximum Upload Slots"))

config.register_block('bandwidth','torrent', BandwithTorrent)


class Download(config.CfgForm):
    title = _("Download")
    download_location = config.ServerFolder(_("Store all downoads in"))
    torrentfiles_location = config.ServerFolder(_("Save .torrent files to"))
    autoadd_location = config.ServerFolder(_("Auto Add folder"), required=False)
    compact_allocation = config.CheckBox(_('Use Compact Allocation'))
    prioritize_first_last_pieces = config.CheckBox(
        _('Prioritize first and last pieces'))

config.register_block('deluge','download', Download)

class Daemon(config.CfgForm):
    title = _("Daemon")
    daemon_port     = forms.IntegerField(_("Port"))
    allow_remote = config.CheckBox(_("Allow Remote Connections"))

config.register_block('deluge','daemon', Daemon)

class Plugins(config.Form):
    title = _("Enabled Plugins")
    _choices = [(p,p) for p in ws.proxy.get_available_plugins()]
    enabled_plugins = config.MultipleChoice(_(""), _choices)

    def initial_data(self):
        return {'enabled_plugins':ws.proxy.get_enabled_plugins()}

    def save(self, value):
        raise forms.ValidationError("SAVE:TODO")

config.register_block('deluge','plugins', Plugins)
