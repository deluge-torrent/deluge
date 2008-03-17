# -*- coding: utf-8 -*-
#
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

#relative:
from webserver_common import ws,REVNO,VERSION
from utils import *
#/relative
from deluge import common
from web import changequery as self_url, template, Storage
import os

class subclassed_render(object):
    """
    adds limited subclassing for templates.
    see: meta.cfg in the template-directory.
    """
    def __init__(self):
        self.apply_cfg()

    def apply_cfg(self):
        self.cache = ws.config.get('cache_templates')
        self.renderers = []
        self.plugin_renderers = []
        self.template_cache = {}

        #load template-meta-data
        cfg_template = ws.config.get('template')
        template_path = os.path.join(ws.webui_path, 'templates/%s/' % cfg_template)
        if not os.path.exists(template_path):
            template_path = os.path.join(ws.webui_path, 'templates/deluge/')
        self.meta = Storage(eval(open(os.path.join(template_path,'meta.cfg')).read()))

        #load renerders
        for template_name in [cfg_template] + list(reversed(self.meta.inherits)):
            self.renderers.append(template.render(
                os.path.join(ws.webui_path, 'templates/%s/' % template_name),cache=False))

    @logcall
    def register_template_path(self, path):
        self.plugin_renderers.append(template.render(path))

    @logcall
    def unregister_template_path(self, path):
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

        raise AttributeError, 'no template named "%s" '  % attr

    def __getitem__(self, item):
        "for plugins/templates"
        return getattr(self, item)

render = subclassed_render()

def error_page(error):
    web.header("Content-Type", "text/html; charset=utf-8")
    web.header("Cache-Control", "no-cache, must-revalidate")
    print render.error(error)

#template-defs:
"""
obsolete:
def category_tabs(torrent_list):
    filter_tabs, category_tabs = get_category_choosers(torrent_list)
    return render.part_categories(filter_tabs, category_tabs)
"""

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

    if vars.sort == id:
        if vars.order == 'down':
            order = 'up'
            active_down = True
        else:
            active_up = True

    return render.sort_column_head(id, name, order, active_up, active_down)

def template_part_stats():
    try:
        return render.part_stats(get_stats())
    except Exception:
        return '[not connected]'

def get_config(var):
    return ws.config.get(var)

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
    return val

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
    'self_url': self_url,
    'fspeed': common.fspeed,
    'fsize': common.fsize,
    'ftime':ftime,
    'render': render, #for easy resuse of templates
    'rev': 'rev.%s'  % (REVNO, ),
    'version': VERSION,
    'getcookie':getcookie,
    'get': lambda (var): getattr(web.input(**{var:None}), var), # unreadable :-(
    'env':ws.env,
    'forms':web.Storage(),
    'enumerate':enumerate

})
#/template-defs

__all__ = ['render']
