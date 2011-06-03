#
# gtkui.py
#
# Copyright (C) 2009-2010 Pedro Algarvio <pedro@algarvio.me>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
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

import gtk
import logging

from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

from common import get_resource

log = logging.getLogger(__name__)

class GtkUI(GtkPluginBase):

    def enable(self):
        log.debug('Enabling %s FreeSpace', self.__class__.__name__)
        self.glade = gtk.glade.XML(get_resource("config.glade"))
        self.prefs = self.glade.get_widget('prefs_box')
        parent = self.prefs.get_parent()
        if parent:
            parent.remove(self.prefs)

#        chk_ap = component.get("Preferences").glade.get_widget('chk_add_paused')
#        downloads_vbox = chk_ap.get_parent().get_parent().get_parent().get_parent()

        downloads_vbox = component.get("Preferences").glade.get_widget('vbox1')
        downloads_vbox.pack_start(self.prefs, False, True, 0)
#        self.prefs.set_parent(frame)

#        component.get("Preferences").add_page("FreeSpace", self.glade.get_widget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs",
                                                     self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs",
                                                     self.on_show_prefs)

        try:
            notifications = component.get("GtkPlugin.Notifications")
            notifications.register_custom_popup_notification(
                "LowDiskSpaceEvent", self.__custom_popup_notification
            )
            notifications.register_custom_blink_notification(
                "LowDiskSpaceEvent", self.__custom_blink_notification
            )
            notifications.register_custom_sound_notification(
                "LowDiskSpaceEvent", self.__custom_sound_notification
            )
        except KeyError:
            pass

        client.register_event_handler("PluginEnabledEvent",
                                      self.__on_plugin_enabled)

        client.register_event_handler("PluginDisabledEvent",
                                      self.__on_plugin_disabled)

    def disable(self):
        component.get("Preferences").remove_page("FreeSpace")
        component.get("PluginManager").deregister_hook("on_apply_prefs",
                                                       self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs",
                                                       self.on_show_prefs)
        try:
            notifications = component.get("GtkPlugin.Notifications")
            notifications.deregister_custom_popup_notification(
                "LowDiskSpaceEvent"
            )
            notifications.deregister_custom_blink_notification(
                "LowDiskSpaceEvent"
            )
            notifications.deregister_custom_sound_notification(
                "LowDiskSpaceEvent"
            )
        except KeyError:
            pass

        client.deregister_event_handler("PluginEnabledEvent",
                                        self.__on_plugin_enabled)

        client.deregister_event_handler("PluginDisabledEvent",
                                        self.__on_plugin_disabled)

    def on_apply_prefs(self):
        log.debug("applying prefs for FreeSpace")
        config = {
            "enabled": self.glade.get_widget('enabled').get_active(),
            "percent": self.glade.get_widget('percent').get_value()
        }
        client.freespace.set_config(config)

    def on_show_prefs(self):
        client.freespace.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.glade.get_widget('enabled').set_active(config['enabled'])
        self.glade.get_widget('percent').set_value(config['percent'])

    def __custom_popup_notification(self, ocupied_percents):
        title = _("Low Free Space")
        message = ''
        for path, percent in ocupied_percents.iteritems():
            message += '%s%%  %s\n' % (percent, path)
        message += '\n'
        return title, message

    def __custom_blink_notification(self, ocupied_percents):
        return True # Yes, do blink

    def __custom_sound_notification(self, ocupied_percents):
        return ''   # Use default sound

    def __on_plugin_enabled(self, plugin_name):
        if plugin_name == 'Notifications':
            notifications = component.get("GtkPlugin.Notifications")
            notifications.register_custom_popup_notification(
                "LowDiskSpaceEvent", self.__custom_popup_notification
            )
            notifications.register_custom_blink_notification(
                "LowDiskSpaceEvent", self.__custom_blink_notification
            )
            notifications.register_custom_sound_notification(
                "LowDiskSpaceEvent", self.__custom_sound_notification
            )

    def __on_plugin_disabled(self, plugin_name):
        pass
#        if plugin_name == 'Notifications':
#            notifications = component.get("GtkPlugin.Notifications")
#            notifications.deregister_custom_popup_notification(
#                "LowDiskSpaceEvent"
#            )
#            notifications.deregister_custom_blink_notification(
#                "LowDiskSpaceEvent"
#            )
#            notifications.deregister_custom_sound_notification(
#                "LowDiskSpaceEvent"
#            )
