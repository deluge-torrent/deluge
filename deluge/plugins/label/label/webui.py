#
# webui.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
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

import os
from deluge.common import fspeed
from deluge.log import LOG as log
from deluge.ui.client import sclient, aclient
from deluge.plugins.webuipluginbase import WebUIPluginBase
from deluge import component

api = component.get("WebPluginApi")
forms = api.forms

#pages:
class options:
    def page(self, label_id,  options , error=None):
        options_form = OptionsForm(options)
        options_form.label_id = label_id
        options_form.full_clean()
        return api.render.label.options(label_id, options_form)

    @api.deco.deluge_page
    def GET(self, label_id):
        return self.page(label_id, sclient.label_get_options(label_id))

    @api.deco.check_session
    def POST(self, label_id):
        post_options = api.utils.get_newforms_data(OptionsForm)
        options = sclient.label_get_options(label_id)

        log.debug(options)
        options.update(dict(post_options))
        log.debug(options)
        options_form = OptionsForm(options)
        options_form.label_id = label_id

        if not options_form.is_valid():
             return self.page(label_id, options,  _("Error setting label options"))
        else:
            error = None

        sclient.label_set_options(label_id, options_form.cleaned_data)
        api.utils.seeother("/config/label")


class add:
    @api.deco.deluge_page
    def GET(self, label_id):
        return api.render.label.options(label_id)

class remove:
    @api.deco.deluge_page
    def GET(self, label_id):
        return api.render.label.options(label_id)

class config_page:
    """for ajaxui."""
    @api.deco.deluge_page
    def GET(self, args):
        labels = sclient.label_get_labels()
        return api.render.label.config_page(labels)


class WebUI(WebUIPluginBase):
    include_javascript = ["/label/data/label.js"]
    urls = [
        ('/label/options/(.*)', options),
        ('/label/add', add),
        ('/label/remove/(.*)', remove),
        ('/label/config', config_page)
    ]

    def enable(self):
        api.config_page_manager.register('plugins', 'label' ,ConfigForm)

    def disable(self):
        api.config_page_manager.deregister('label')

#options:
    """
    todo (see gtkui)
    sensitive_groups = [
        ("apply_max", ["max_download_speed", "max_upload_speed", "max_upload_slots", "max_connections"]),
        ("apply_queue", ["is_auto_managed", "stop_at_ratio"]),
        ("stop_at_ratio", ["remove_at_ratio", "stop_ratio"]), #nested
        ("apply_move_completed", ["move_completed"]),
        ("move_completed", ["move_completed_path"]), #nested
        ("auto_add", ["auto_add_trackers"])
        ]
"""
class OptionsForm(forms.Form):

    #load/save:
    def initial_data(self):
        return sclient.label_get_options(self.label_id)

    #maximum:
    apply_max = forms.CheckBox(_("apply_max"))
    max_download_speed = forms.DelugeInt(_("max_download_speed"))
    max_upload_speed = forms.DelugeInt(_("max_upload_speed"))
    max_upload_slots = forms.DelugeInt(_("max_upload_slots"))
    max_connections = forms.DelugeInt(_("max_connections"))

    #queue:
    apply_queue = forms.CheckBox(_("apply_queue"))
    is_auto_managed = forms.CheckBox(_("is_auto_managed"))
    stop_at_ratio = forms.CheckBox(_("stop_at_ratio"))
    stop_ratio = forms.DelugeFloat(_("stop_ratio"),  required=False)
    remove_at_ratio = forms.CheckBox(_("remove_at_ratio"))

    #location:
    apply_move_completed = forms.CheckBox(_("apply_move_completed"))
    move_completed = forms.CheckBox(_("move_completed"))
    move_completed_path = forms.CharField(label=_("move_completed_path"), required=False)

    #tracker:
    auto_add = forms.CheckBox(_("auto_add"))
    auto_add_trackers = forms.StringList(_("auto_add_trackers"))



#config:
class ConfigForm(forms.Form):
    """
    custom config page
    too complex for the default config framework
    """
    #meta:
    title = _("Label")
    info = _("Work in progress..")

    #load/save:
    def initial_data(self):
        return sclient.label_get_config()

    def save(self, data):
        cfg = dict(data)
        sclient.label_set_config(cfg)

    def pre_html(self):
        """ custom config html/template"""
        labels = sclient.label_get_labels()
        return api.render.label.config(labels)



    #django newforms magic: define config fields:
    #test = forms.CharField(label=_("Test config value"))
