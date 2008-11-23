#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
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
# 	Boston, MA    02110-1301, USA.
#


import os
from deluge.log import LOG as log
from deluge.ui.client import sclient
from deluge import component

api = component.get("WebPluginApi")
forms = api.forms

class LabelUpdateCfgForm(forms.Form):
    """
    a config form based on django forms.
    see webui.lib.newforms_plus, config_forms, etc.
    """
    #meta:
    title = _("Labels")

    def get_selected(self):
        selected = api.web.input(label = None).label
        labels = sclient.label_get_labels()
        if not selected:
            if labels:
                selected = labels[0]
        return selected

    def pre_html(self):
        selected = self.get_selected()
        html = _("Select Label") + ":"
        for label in sclient.label_get_labels():
            html += """
            <a href="/config/label_update?label=%(label)s">%(label)s</a> &nbsp;""" % {"label":label}
        html += "<h2>%s</h2>" % selected
        return html
    #load/save:
    def initial_data(self):
        label_id = self.get_selected()
        return sclient.label_get_options(label_id)

    def save(self, data):
        label_id = self.get_selected()
        apply = data.apply
        delete = data.delete

        if delete:
            sclient.label_remove(label_id)
            raise Exception("DELETED")
        else:
            del data["apply"]
            del data["delete"]
            sclient.label_set_options(label_id, dict(data), apply)

    #input fields :
    max_connections = forms.DelugeInt(_("Maximum Connections"))
    max_download_speed = forms.DelugeFloat(_("Maximum Download Speed (Kib/s)"))
    max_upload_speed = forms.DelugeFloat(_("Maximum Upload Speed (Kib/s)"))
    max_upload_slots = forms.DelugeInt(_("Maximum Upload Slots"))

    apply =  forms.CheckBox(_("Apply"))
    delete =  forms.CheckBox(_("Delete"))



class LabelAddCfgForm(forms.Form):
    """
    a config form based on django forms.
    see webui.lib.newforms_plus, config_forms, etc.
    """
    #meta:
    title = _("Add Label")

    #load/save:
    def initial_data(self):
        return {    }

    def save(self, data):
        sclient.label_add(data.label)

    label = forms.CharField(_("Label"))

class LabelCfgForm(forms.Form):
    """
    global settings.
    """
    #meta:
    title = _("General")

    #load/save:
    def initial_data(self):
        return sclient.label_get_global_options()

    def save(self, data):
        return sclient.label_set_global_options(dict(data))

    hide_zero_hits =  forms.CheckBox(_("Hide filter items with 0 hits"))
    #gtk_alfa =  forms.CheckBox(_("gtk_alfa"))




def register():
    api.config_page_manager.register('label','label_general',LabelCfgForm)
    api.config_page_manager.register('label','label_update',LabelUpdateCfgForm)
    api.config_page_manager.register('label','label_add',LabelAddCfgForm)

def unregister():
    api.config_page_manager.unregister('label_general')
    api.config_page_manager.unregister('label_update')
    api.config_page_manager.unregister('label_add')











