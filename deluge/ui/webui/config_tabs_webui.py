#!/usr/bin/env python
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


from deluge.ui.client import sclient as proxy
from deluge.log import LOG as log


import utils
import lib.newforms_plus as forms
import config_forms
from deluge import component
from render import render

config_page = component.get("ConfigPageManager")
plugins = component.get("WebPluginManager")


class Template(config_forms.WebCfgForm):
    title = _("Template")

    _templates = [(t,t) for t in render.get_templates()]
    _button_choices = enumerate([_('Text and image'),  _('Image Only')
        ,  _('Text Only')])

    template = forms.ChoiceField( label=_("Template"), choices = _templates)
    button_style = forms.IntChoiceField(_("Button style"),_button_choices)
    refresh_secs =  forms.IntegerField(label= _("Auto refresh (seconds)"), min_value=2, max_value=60*60)
    cache_templates = forms.CheckBox(_("Cache templates"))

    def post_save(self):
        from render import render
        render.apply_cfg()

class Server(config_forms.WebCfgForm):
    title = _("Server")
    info = _("Manually restart webui to apply changes.")

    port = forms.IntegerField(label = _("Port"),min_value=80)
    https =  forms.CheckBox(_("Https"))

    def validate(self, data):
        import os
        from deluge.common import get_default_config_dir

        if data.https:
            cert_path = os.path.join(get_default_config_dir("ssl") ,"deluge.cert.pem" )
            if not os.path.exists (cert_path):
                raise forms.ValidationError(_("Certificate not found at '%s'" % cert_path))
            key_path = os.path.join(get_default_config_dir("ssl") ,"deluge.key.pem" )
            if not os.path.exists (key_path):
                raise forms.ValidationError(_("Key not found at '%s'" % key_path))


    def post_save(self):
        pass
        #raise forms.ValidationError(
        #       )

class Password(forms.Form):
    title = _("Password")

    old_pwd = forms.Password(_("Current Password"))
    new1 = forms.Password(_("New Password"))
    new2 = forms.Password(_("New Password (Confirm)"))

    def save(self,data):
        utils.update_pwd(data.new1)

    def validate(self, data):
        if not utils.check_pwd(data.old_pwd):
            raise forms.ValidationError(_("Old password is invalid"))
        if data.new1 <> data.new2:
            raise forms.ValidationError(
                _("New Password is not equal to New Password(confirm)"))

    def post_save(self):
        utils.end_session()
        #raise forms.ValidationError(_("Password changed,please login again"))

class Sidebar(config_forms.WebCfgForm):
    title = _("Sidebar")
    show_sidebar = forms.CheckBox(_("Show sidebar"))
    sidebar_show_zero = forms.CheckBox(_("Show zero hits"))
    sidebar_show_trackers  = forms.CheckBox(_("Show trackers"))
    show_keyword_search = forms.CheckBox(_("Show keyword search"))

config_page.register('webui','template', Template)
config_page.register('webui','server',Server)
config_page.register('webui','password',Password)
config_page.register('webui','sidebar',Sidebar)
