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


#relative:

from utils import *
import utils
#/relative
from deluge import common
from deluge import component
from web import template, Storage
import os
from deluge.configmanager import ConfigManager

config = ConfigManager("webui06.conf")
page_manager = component.get("PageManager")


class subclassed_render(object):
    """
    adds limited subclassing for templates.
    see: meta.cfg in the template-directory.
    """
    def __init__(self):
        self.apply_cfg()
        self.plugin_renderers = []

    def apply_cfg(self):
        self.cache = config['cache_templates']
        self.renderers = []
        self.template_cache = {}
        self.webui_path = os.path.dirname(__file__)

        #load template-meta-data
        self.cfg_template = config['template']
        template_path = os.path.join(self.webui_path, 'templates/%s/' % self.cfg_template)
        if not os.path.exists(template_path):
            template_path = os.path.join(self.webui_path, 'templates/white/')
        self.meta = Storage(eval(open(os.path.join(template_path,'meta.cfg')).read()))

        #load renerders
        for template_name in [self.cfg_template] + list(reversed(self.meta.inherits)):
            self.renderers.append(template.render(
                os.path.join(self.webui_path, 'templates/%s/' % template_name),cache=False))

    @logcall
    def register_template_path(self, path):
        self.plugin_renderers.append(template.render(path , cache=False))

    @logcall
    def deregister_template_path(self, path):
        for i, renderer in list(ennumerate(self.plugin_renderers)):
            if renderer.loc == path:
                del self.plugin_renderers[i]
                return

    def __getattr__(self, attr):
        if self.cache and attr in self.template_cache:
            return self.template_cache[attr]

        for renderer in self.renderers + self.plugin_renderers:
            if hasattr(renderer, attr):
                self.template_cache[attr] = getattr(renderer, attr)
                return getattr(renderer, attr)
        raise AttributeError, 'no template named "%s" in template-dirs:%s'  % (attr,
            [r.loc for r in self.renderers + self.plugin_renderers] )

    def __getitem__(self, item):
        "for plugins/templates"
        return getattr(self, item)

    @staticmethod
    def get_templates():
        "utility method."
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        return [dirname for dirname
            in os.listdir(template_path)
            if os.path.isdir(os.path.join(template_path, dirname))
                and not dirname.startswith('.')]

    @staticmethod
    def set_global(key, val):
        template.Template.globals[key] = val

render = subclassed_render()

def error_page(error):
    web.header("Content-Type", "text/html; charset=utf-8")
    web.header("Cache-Control", "no-cache, must-revalidate")
    print render.error(error)


def template_crop_middle(text, maxlen):
    try:
        if len(text) > maxlen:
            half = (maxlen / 2) - 2
            return text[0:half ] + '...' + text[-half:]
    except:
        return "[ERROR NOT A STRING:(%s)]" % text
    return text


def template_sort_head(id,name):
    #got tired of doing these complex things inside templetor..
    vars = web.input(sort = None, order = None)
    active_up = False
    active_down = False
    order = 'down'

    if not vars.sort: #no arguments, default to coockies.
        vars.update(cookies())


    if vars.sort == id:
        if vars.order == 'down':
            order = 'up'
            active_down = True
        else:
            active_up = True

    return render.sort_column_head(id, name, order, active_up, active_down)

def template_part_stats():
    try:
        return render.part_stats(Storage(sclient.get_stats()))
    except Exception, e:
        return str(e)

def get_config(var):
    return config[var]

irow = 0
def altrow(reset = False):
    global irow
    if reset:
        irow = 1
        return
    irow +=1
    irow = irow % 2
    return "altrow%s" % irow

def deluge_int(val):
    if val == -1 :
        return "∞"
    return val

def ftime(val):
    if val <= 0:
        return _("∞")
    return common.ftime(val)

def template_get(key):
    val = getattr(web.input(**{key:None}), key)
    if not val:
        val = getcookie(key)
    return val or ""

def id_to_label(text):
    "translated capitalize"
    text = text.replace("_"," ")
    text = text.capitalize()
    return _(text)

template.Template.globals.update({
    'sort_head': template_sort_head,
    'part_stats':template_part_stats,
    'crop': template_crop_middle,
    'crop_left': template_crop_middle,
    '_': _ , #gettext/translations
    'str': str, #because % in templetor is broken.
    'int':int,
    'len':len,
    'deluge_int':deluge_int,
    'sorted': sorted,
    'altrow':altrow,
    'get_config': get_config,
    'self_url': utils.self_url,
    'fspeed': common.fspeed,
    'fsize': common.fsize,
    'ftime':ftime,
    'render': render, #for easy resuse of templates
    'version':common.get_version() ,
    'rev': common.get_revision(),
    'getcookie':getcookie,
    'get': template_get,
    #'env':'0.6',
    'forms':web.Storage(),
    'enumerate':enumerate,
    'base':'', #updated when running within apache.
    'id_to_label':id_to_label,
    'include_javascript':page_manager.include_javascript,
    'ajax_javascript':page_manager.include_javascript,
    'is_auto_refreshed':False
})
#/template-defs

__all__ = ['render']
