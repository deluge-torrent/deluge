# -*- coding: utf-8 -*-
#
# deluge_webserver.py
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


from deluge.ui.client import sclient
from deluge.log import LOG as log

import utils

import lib.newforms_plus as forms
import config_forms
from deluge import component

config_page = component.get("ConfigPageManager")

class NetworkPorts(config_forms.CfgForm ):
    title = _("Ports")
    _port_from =  forms.IntegerField(label= _("From"),min_value = 0, max_value=65535)
    _port_to = forms.IntegerField(label = _("To"),min_value = 0, max_value=65535)
    random_port = forms.CheckBox(label = _("Random"))

    def initial_data(self):
        data = config_forms.CfgForm.initial_data(self)
        data['_port_from'] , data['_port_to'] = data['listen_ports']
        return data

    def save(self,data):
        data['listen_ports'] = [data['_port_from'] , data['_port_to'] ]
        del(data['_port_from'])
        del(data['_port_to'])
        config_forms.CfgForm.save(self, data)

    def validate(self, data):
        if (data['_port_to'] < data['_port_from']):
            raise forms.ValidationError('"Port from" must be greater than "Port to"')

    def post_html(self):
        return """
        <ul>
            <li>Active port:%(active_port)s </li>
            <li><a href="http://deluge-torrent.org/test-port.php?port=%(active_port)s">Test active port</li>
        </ul>
        """ % {'active_port':sclient.get_listen_port()}

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

class Proxy(config_forms.CfgForm):
    title = _("Proxy")
    _type_choices = list(enumerate(
        [_("None"), _("Socksv4"), _("Socksv5"), _("Socksv5 W/ Auth"),_("HTTP"), _("HTTP W/ Auth")]))

    proxy_type =  forms.IntChoiceField(_("Type"), _type_choices)
    proxy_server =forms.CharField(label= _("Host"),required=False)
    proxy_port = forms.IntegerField(label= _("Port"),min_value = 0, max_value=65535 , required=False)
    proxy_username = forms.CharField(label= _("Username"), required=False)
    proxy_password = forms.Password(label= _("Password"), required=False)

config_page.register('network','proxy', Proxy)

class BandwithGlobal(config_forms.CfgForm):
    title = _("Global")
    info = _("-1 = Unlimited")
    max_connections_global = forms.DelugeInt(_("Maximum Connections"))
    max_download_speed = forms.DelugeFloat(_("Maximum Download Speed (Kib/s)"))
    max_upload_speed = forms.DelugeFloat(_("Maximum Upload Speed (Kib/s)"))
    max_upload_slots_global = forms.DelugeInt(_("Maximum Upload Slots"))

    max_half_open_connections = forms.DelugeInt(_("Maximum Half-Open Connections"))
    max_connections_per_second = forms.DelugeInt(_("Maximum Connection Attempts per Second"))
    ignore_limits_on_local_network = forms.CheckBox(_("Ignore limits on local network"))
    rate_limit_ip_overhead = forms.CheckBox(_("Rate Limit IP Overhead"))


config_page.register('bandwidth','global', BandwithGlobal)

class BandwithTorrent(config_forms.CfgForm):
    title = _("Per Torrent")
    info = _("-1 = Unlimited")
    max_connections_per_torrent = forms.DelugeInt(_("Maximum Connections"))
    max_download_speed_per_torrent = forms.DelugeFloat(_("Maximum Download Speed (Kib/s)"))
    max_upload_speed_per_torrent = forms.DelugeFloat(_("Maximum Upload Speed (Kib/s)"))
    max_upload_slots_per_torrent = forms.DelugeInt(_("Maximum Upload Slots"))

config_page.register('bandwidth','torrent', BandwithTorrent)

class Download(config_forms.CfgForm):
    title = _("Download")
    download_location = forms.ServerFolder(_("Store all downoads in"))
    torrentfiles_location = forms.ServerFolder(_("Save .torrent files to"))
    autoadd_location = forms.ServerFolder(_("Auto Add folder"), required=False)
    autoadd_enable = forms.CheckBox(_("Auto Add enabled"))
    compact_allocation = forms.CheckBox(_('Use Compact Allocation'))
    prioritize_first_last_pieces = forms.CheckBox(_('Prioritize first and last pieces'))
    #default_private = forms.CheckBox(_('Set private flag by default'))

config_page.register('deluge','download', Download)

class Daemon(config_forms.CfgForm):
    title = _("Daemon")
    info = _("Restart daemon and webui after changing these settings")
    daemon_port     = forms.IntegerField(_("Port"))
    allow_remote = forms.CheckBox(_("Allow Remote Connections"))

config_page.register('deluge','daemon', Daemon)

class Queue(config_forms.CfgForm):
    title = _("Queue")
    info = _("-1 = unlimited")

    queue_new_to_top = forms.CheckBox(_("Queue new torrents to top"))


    #total_downloading = forms.DelugeInt(_("Total active downloading"))
    max_active_limit = forms.DelugeInt(_("Total active torrents"))
    max_active_downloading = forms.DelugeInt(_("Total active downloading"))
    max_active_seeding = forms.DelugeInt(_("Total active seeding"))


    share_ratio_limit = forms.FloatField(min_value=-1)
    seed_time_ratio_limit = forms.FloatField(min_value=-1)
    seed_time_limit = forms.FloatField(min_value=-1)

    stop_seed_at_ratio = forms.CheckBox(_("Stop seeding when ratio reaches"))
    #stop_ratio = forms.FloatField(min_value=-1)
    remove_seed_at_ratio = forms.CheckBox(_("Remove torrent when ratio reached"))
    stop_seed_ratio = forms.FloatField(min_value=-1)

config_page.register('deluge','queue', Queue)

"""
Will become a plugin, saved for later use.
class Notification(config_forms.CfgForm):
    title = _("Notification")
    _security_choices =  [(t,t) for t in [None,"SSL","TLS"]]
    ntf_email = forms.EmailField(label=_("Email"), required=False)
    ntf_server =forms.CharField(label= _("Server"), required=False)
    ntf_username = forms.CharField(label= _("Username"), required=False)
    ntf_password = forms.CharField(label= _("Password"), required=False)
    ntf_security = forms.ChoiceField( label=_("Security"), choices = _security_choices )

config_page.register('deluge','notification', Notification)
"""

class Plugins(forms.Form):
    title = _("Enabled Plugins")

    enabled_plugins = forms.LazyMultipleChoice(
        choices_getter = lambda: [(p,p) for p in sclient.get_available_plugins()]
    )

    def initial_data(self):
        return {'enabled_plugins':sclient.get_enabled_plugins()}

    def save(self, data):
        new_plugins = data.enabled_plugins
        old_plugins = sclient.get_enabled_plugins()

        enable = [p for p in new_plugins if p not in old_plugins]
        disable = [p for p in old_plugins if p not in new_plugins]


        plugin_manager = component.get("WebPluginManager")
        for p in enable:
            sclient.enable_plugin(p)
            plugin_manager.enable_plugin(p)

        for p in disable:
            sclient.disable_plugin(p)
            plugin_manager.disable_plugin(p)

config_page.register('deluge','plugins', Plugins)

