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


import lib.newforms_plus as forms
import page_decorators as deco
import web
from deluge.ui.client import sclient as proxy
from deluge.log import LOG as log

from render import render
from utils import seeother
import sys
import os
import utils

from deluge import component
from deluge.configmanager import ConfigManager

config = ConfigManager("webui06.conf")
config_page_manager = component.get("ConfigPageManager")

class WebCfgForm(forms.Form):
    "config base for webui"
    def initial_data(self):
        return config.config

    def save(self, data):
        utils.validate_config(data)
        for key, value in data.iteritems():
            config[key] = value
        config.save()

class CfgForm(forms.Form):
    "config base for deluge-cfg"
    def initial_data(self):
        return proxy.get_config()
    def save(self, data):
        proxy.set_config(dict(data))

class config_page:
    """
    web.py config page
    """
    def get_form_class(self,name):
        try:
            return config_page_manager.blocks[name]
        except KeyError:
            raise Exception('no config page named:"%s"' % name)

    @deco.deluge_page
    def GET(self, name):
        if name == '':
            return seeother('/config/template')

        form_class = self.get_form_class(name)
        f = form_class()
        f.full_clean()
        return self.render(f , name)

    @deco.deluge_page
    def POST(self,name):

        form_class = self.get_form_class(name)
        form_data = web.Storage(utils.get_newforms_data(form_class))
        form = form_class(form_data)
        if form.is_valid():
            log.debug('save config %s' % form_data)
            try:
                form.start_save()
                return self.render(form , name, _('These changes were saved'))
            except forms.ValidationError, e:
                log.debug(e.message)
                return self.render(form , name, error = e.message)
        else:
            return self.render(form , name,
                error= _('Correct the errors above and try again'))

    def render(self, f , name , message = '' , error=''):
        return render.config(config_page_manager.groups, config_page_manager.blocks, f, name , message , error)

def register():
    component.get("PageManager").register_page("/config/(.*)", config_page)

