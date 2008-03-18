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


import utils
from webserver_common import ws, log
import lib.newforms_plus as forms
import config_forms
from deluge import component

config_page = component.get("ConfigPageManager")
plugins = component.get("WebPluginManager")

class Template(config_forms.WebCfgForm):
    title = _("Template")

    _templates = [(t,t) for t in ws.get_templates()]
    _button_choices = enumerate([_('Text and image'),  _('Image Only')
        ,  _('Text Only')])

    template = forms.ChoiceField( label=_("Template"), choices = _templates)
    button_style = forms.IntChoiceField(_("Button style"),_button_choices)
    cache_templates = forms.CheckBox(_("Cache templates"))

    def post_save(self):
        from render import render
        render.apply_cfg()

class Server(config_forms.WebCfgForm):
    title = _("Server")
    port = forms.IntegerField(label = _("Port"),min_value=80)
    use_https = forms.CheckBox(_("Use https"))

    try:
        import OpenSSL
    except ImportError:
        info = _("pyopenssl not installed, install this for https.")

    def post_save(self):
        pass
        #raise forms.ValidationError(
        #       _("Manually restart server to apply these changes."))

class Password(forms.Form):
    title = _("Password")

    old_pwd = forms.Password(_("Current Password"))
    new1 = forms.Password(_("New Password"))
    new2 = forms.Password(_("New Password (Confirm)"))

    def save(self,data):
        ws.update_pwd(data.new1)
        ws.save_config()

    def validate(self, data):
        if not ws.check_pwd(data.old_pwd):
            raise forms.ValidationError(_("Old password is invalid"))
        if data.new1 <> data.new2:
            raise forms.ValidationError(
                _("New Password is not equal to New Password(confirm)"))

    def post_save(self):
        utils.end_session()
        #raise forms.ValidationError(_("Password changed,please login again"))

class WebUiPlugins(forms.Form):
    title = _("WebUi Plugins")

    _choices = [(p,p) for p in plugins.get_available_plugins()]
    enabled_plugins = forms.MultipleChoice(_(""), _choices)

    def initial_data(self):
        return {'enabled_plugins':plugins.get_enabled_plugins()}

    def save(self, data):
        log.debug(data)
        for plugin_name in data['enabled_plugins']:
            plugins.enable_plugin(plugin_name)

config_page.register('webui','template', Template)
config_page.register('webui','server',Server)
config_page.register('webui','password',Password)
config_page.register('webui','webuiplugins',WebUiPlugins)
