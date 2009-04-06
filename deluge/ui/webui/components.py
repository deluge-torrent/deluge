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

"""
deluge components.

MenuManager:add torrent-menu-items and torrent-detail tabs.
PageManager: add pages(urls)
PluginManager: deluge plugin manager
ConfigPageManager: add config pages(tabs)

These managers/components are accesible as:

from deluge import component
manager = component.get("ClassName")

"""
from deluge import component
import lib.newforms_plus as forms
from lib.egg_handler import egg_handler
from lib.egg_render import egg_render
from deluge.ui.client import aclient
from deluge import component, pluginmanagerbase
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class TOOLBAR_FLAGS:
    generic = 0
    torrent = 1
    torrent_list = 2

class MenuManager(component.Component):
    TOOLBAR_FLAGS = TOOLBAR_FLAGS
    def __init__(self):
        component.Component.__init__(self, "MenuManager")
        self.admin_pages = [] #[(title, url),..]
        self.detail_tabs = [] #[(title, url),..]
        self.toolbar_items = [] #((id,title ,flag ,method ,url ,image ),.. )


        #register vars in template.
        from render import template
        template.Template.globals["admin_pages"] = self.admin_pages
        template.Template.globals["detail_tabs"] = self.detail_tabs
        template.Template.globals["toolbar_items"] = self.toolbar_items


    def register_toolbar_item(self, id, title, image, flag, method, url, important):
        self.toolbar_items.append((id, title, image, flag, method, url, important))

    def deregister_toolbar_item(self, item_id):
        for (i, toolbar) in enumerate(admin_pages):
            if toolbar[0] == item_id:
                del self.toolbar_items[i]

    #admin:
    def register_admin_page(self, id, title, url):
        self.admin_pages.append((id, title, url))

    def deregister_admin_page(page_id):
        for (i, (id, title, url)) in list(enumerate(admin_pages)):
            if id == page_id:
                del self.admin_pages[i]
                return

    #detail:
    def register_detail_tab(self, id, title, page):
        self.detail_tabs.append((id, title, page))

    def deregister_detail_tab(self, tab_id):
        for (i, (id, title, tab)) in list(enumerate(detail_tabs)):
            if id == tab_id:
                del self.detail_tabs[i]
                return

class PageManager(component.Component):
    """
    web,py 0.2 mapping hack..
    see deluge_webserver.py
    """
    def __init__(self):
        component.Component.__init__(self, "PageManager")
        self.page_classes = {}
        self.urls = []
        self.include_javascript = []
        self.ajax_javascript = []

    def register_pages(self, url_list, class_list):
        self.urls += url_list
        self.page_classes.update(class_list)

    def register_page(self, url, klass, use_module=True):
        if use_module:
            name = klass.__module__ + "." + klass.__name__
        else:
            name = klass.__name__
        self.urls.append(url)
        self.urls.append(name)
        self.page_classes[name] = klass

    def deregister_page(self, url):
        raise NotImplemenetedError()
        #self.page_classes[klass.__name__] = None

class PluginManager(pluginmanagerbase.PluginManagerBase,
    component.Component):
    def __init__(self):
        component.Component.__init__(self, "WebPluginManager")
        self.config = ConfigManager("webui06.conf")
        pluginmanagerbase.PluginManagerBase.__init__(
            self, "webui06.conf", "deluge.plugin.webui")

    def start(self):
        """Start the plugin manager"""
        # Update the enabled_plugins from the core
        log.debug("start webui plugin manager")
        aclient.get_enabled_plugins(self._on_get_enabled_plugins)
        aclient.force_call(block=True)

    def stop(self):
        # Disable the plugins
        self.disable_plugins()

    def _on_get_enabled_plugins(self, enabled_plugins):

        log.debug("..Webui has these plugins enabled: %s", enabled_plugins)

        log.debug("abababab")
        log.debug(self.config)

        self.config.config["enabled_plugins"] = enabled_plugins

        # Enable the plugins that are enabled in the config and core
        log.debug(self.enable_plugins)
        try:
            self.enable_plugins()
        except Exception, e:
            log.debug(e)


class ConfigPageManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, "ConfigPageManager")
        self.groups = []
        self.blocks = forms.django.utils.datastructures.SortedDict()

    def register(self, group, name, form):
        if not group in self.groups:
            self.groups.append(group)
        form.group = group
        self.blocks[name] = form

    def deregister(self, name):
        del self.blocks[name]

class PluginApi(component.Component):
    """
    """
    def __init__(self):
        component.Component.__init__(self, "WebPluginApi")
        import web
        from render import render
        import page_decorators as deco
        import utils
        import lib.newforms_plus as forms

        self.egg_handler = egg_handler
        self.egg_render = egg_render
        self.render  = render
        self.web = web
        self.deco = deco
        self.forms = forms
        self.page_manager = component.get("PageManager")
        self.config_page_manager = component.get("ConfigPageManager")
        self.menu_manager = component.get("MenuManager")
        self.utils = utils

def register():
    __page_manager = PageManager()
    __plugin_manager = PluginManager()
    __menu_manager = MenuManager()
    __config_page_manager =  ConfigPageManager()
    __plugin_api =  PluginApi()


if __name__ == "__main__":
    register()



