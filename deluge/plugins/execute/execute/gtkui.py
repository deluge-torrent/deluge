#
# gtkui.py
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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
import gtk
import pkg_resources

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

EXECUTE_ID = 0
EXECUTE_EVENT = 1
EXECUTE_COMMAND = 2

EVENT_MAP = {
    "complete": _("Torrent Complete"),
    "added": _("Torrent Added")
}

EVENTS = ["complete", "added"]

class ExecutePreferences(object):
    def __init__(self, plugin):
        self.plugin = plugin
    
    def load(self):
        log.debug("Adding Execute Preferences page")
        self.glade = gtk.glade.XML(self.get_resource("execute_prefs.glade"))
        self.glade.signal_autoconnect({
            "on_add_button_clicked": self.on_add_button_clicked
        })
        
        events = self.glade.get_widget("event_combobox")
        
        store = gtk.ListStore(str, str)
        for event in EVENTS:
            event_label = EVENT_MAP[event]
            store.append((event_label, event))
        events.set_model(store)

        self.plugin.add_preferences_page(_("Execute"),
            self.glade.get_widget("execute_box"))
        self.plugin.register_hook("on_show_prefs", self.load_commands)
        self.plugin.register_hook("on_apply_prefs", self.on_apply_prefs)

    def unload(self):
        self.plugin.remove_preferences_page(_("Execute"))
        self.plugin.deregister_hook("on_apply_prefs", self.on_apply_prefs)
        self.plugin.deregister_hook("on_show_prefs", self.load_commands)

    def get_resource(self, filename):
        return pkg_resources.resource_filename("execute", os.path.join("data",
            filename))
    
    def load_commands(self):
        def on_get_commands(commands):
            vbox = self.glade.get_widget("commands_vbox")
            for command in commands:
                command_id, event, command = command
                log.debug("Adding command `%s`", command_id)
                hbox = gtk.HBox(False, 0)
                label = gtk.Label(EVENT_MAP[event])
                entry = gtk.Entry()
                entry.set_text(command)
                hbox.pack_start(label, padding = 5)
                hbox.pack_start(entry)
                vbox.pack_start(hbox)
                hbox.show_all()
        client.execute.get_commands().addCallback(on_get_commands)
    
    def on_add_button_clicked(self, *args):
        command = self.glade.get_widget("command_entry").get_text()
        events = self.glade.get_widget("event_combobox")
        event = events.get_model()[events.get_active()][1]
        client.execute.add_command(event, command)

    def on_apply_prefs(self):
        options = {}
        #update options dict here.
        client.label.set_config(options)

class GtkUI(GtkPluginBase):    
    
    def enable(self):
        self.plugin = component.get("PluginManager")
        self.preferences = ExecutePreferences(self.plugin)
        self.preferences.load()

    def disable(self):
        self.preferences.unload()
