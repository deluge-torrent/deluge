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
    "added": _("Torrent Added"),
    "removed": _("Torrent Removed")
}

EVENTS = ["complete", "added", "removed"]

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
        events.set_active(0)

        self.plugin.add_preferences_page(_("Execute"),
            self.glade.get_widget("execute_box"))
        self.plugin.register_hook("on_show_prefs", self.load_commands)
        self.plugin.register_hook("on_apply_prefs", self.on_apply_prefs)

        self.load_commands()

        client.register_event_handler("ExecuteCommandAddedEvent", self.on_command_added_event)
        client.register_event_handler("ExecuteCommandRemovedEvent", self.on_command_removed_event)

    def unload(self):
        self.plugin.remove_preferences_page(_("Execute"))
        self.plugin.deregister_hook("on_apply_prefs", self.on_apply_prefs)
        self.plugin.deregister_hook("on_show_prefs", self.load_commands)

    def get_resource(self, filename):
        return pkg_resources.resource_filename("execute", os.path.join("data",
            filename))

    def add_command(self, command_id, event, command):
        log.debug("Adding command `%s`", command_id)
        vbox = self.glade.get_widget("commands_vbox")
        hbox = gtk.HBox(False, 5)
        hbox.set_name(command_id + "_" + event)
        label = gtk.Label(EVENT_MAP[event])
        entry = gtk.Entry()
        entry.set_text(command)
        button = gtk.Button()
        button.set_name("remove_%s" % command_id)
        button.connect("clicked", self.on_remove_button_clicked)

        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)
        button.set_image(img)

        hbox.pack_start(label, False, False)
        hbox.pack_start(entry)
        hbox.pack_start(button, False, False)
        hbox.show_all()
        vbox.pack_start(hbox)

    def remove_command(self, command_id):
        vbox = self.glade.get_widget("commands_vbox")
        children = vbox.get_children()
        for child in children:
            if child.get_name().split("_")[0] == command_id:
                vbox.remove(child)
                break

    def clear_commands(self):
        vbox = self.glade.get_widget("commands_vbox")
        children = vbox.get_children()
        for child in children:
            vbox.remove(child)

    def load_commands(self):
        def on_get_commands(commands):
            self.clear_commands()
            log.debug("on_get_commands: %s", commands)
            for command in commands:
                command_id, event, command = command
                self.add_command(command_id, event, command)

        client.execute.get_commands().addCallback(on_get_commands)

    def on_add_button_clicked(self, *args):
        command = self.glade.get_widget("command_entry").get_text()
        events = self.glade.get_widget("event_combobox")
        event = events.get_model()[events.get_active()][1]
        client.execute.add_command(event, command)

    def on_remove_button_clicked(self, widget, *args):
        command_id = widget.get_name().replace("remove_", "")
        client.execute.remove_command(command_id)

    def on_apply_prefs(self):
        vbox = self.glade.get_widget("commands_vbox")
        children = vbox.get_children()
        for child in children:
            command_id, event = child.get_name().split("_")
            for widget in child.get_children():
                if type(widget) == gtk.Entry:
                    command = widget.get_text()
            client.execute.save_command(command_id, event, command)

    def on_command_added_event(self, command_id, event, command):
        log.debug("Adding command %s: %s", event, command)
        self.add_command(command_id, event, command)

    def on_command_removed_event(self, command_id):
        log.debug("Removing command %s", command_id)
        self.remove_command(command_id)

class GtkUI(GtkPluginBase):

    def enable(self):
        self.plugin = component.get("PluginManager")
        self.preferences = ExecutePreferences(self.plugin)
        self.preferences.load()

    def disable(self):
        self.preferences.unload()
