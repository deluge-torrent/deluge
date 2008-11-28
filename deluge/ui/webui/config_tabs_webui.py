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
    refresh_secs =  forms.IntegerField(label=_("Auto refresh (seconds)"), min_value=2, max_value=60*60)
    cache_templates = forms.CheckBox(_("Cache templates"))

    def post_save(self):
        from render import render
        render.apply_cfg()

class Server(config_forms.WebCfgForm):
    title = _("Server")
    port = forms.IntegerField(label = _("Port"),min_value=80)

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

config_page.register('webui','template', Template)
config_page.register('webui','server',Server)
config_page.register('webui','password',Password)
