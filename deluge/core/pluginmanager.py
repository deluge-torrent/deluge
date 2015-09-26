#
# pluginmanager.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
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


"""PluginManager for Core"""

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from deluge.event import PluginEnabledEvent, PluginDisabledEvent
import deluge.pluginmanagerbase
import deluge.component as component
from deluge.log import LOG as log

class PluginManager(deluge.pluginmanagerbase.PluginManagerBase,
    component.Component):
    """PluginManager handles the loading of plugins and provides plugins with
    functions to access parts of the core."""

    def __init__(self, core):
        component.Component.__init__(self, "CorePluginManager")

        self.status_fields = {}

        # Call the PluginManagerBase constructor
        deluge.pluginmanagerbase.PluginManagerBase.__init__(
            self, "core.conf", "deluge.plugin.core")

    def start(self):
        # Enable plugins that are enabled in the config
        self.enable_plugins()

    def stop(self):
        # Disable all enabled plugins
        self.disable_plugins()

    def shutdown(self):
        self.stop()

    def update_plugins(self):
        for plugin in self.plugins.keys():
            if hasattr(self.plugins[plugin], "update"):
                try:
                    self.plugins[plugin].update()
                except Exception, e:
                    log.exception(e)

    def enable_plugin(self, name):
        if name not in self.plugins:
            super(PluginManager, self).enable_plugin(name)
            if name in self.plugins:
                component.get("EventManager").emit(PluginEnabledEvent(name))

    def disable_plugin(self, name):
        if name in self.plugins:
            super(PluginManager, self).disable_plugin(name)
            if name not in self.plugins:
                component.get("EventManager").emit(PluginDisabledEvent(name))

    def get_status(self, torrent_id, fields):
        """Return the value of status fields for the selected torrent_id."""
        status = {}
        if len(fields) == 0:
            fields = self.status_fields.keys()
        for field in fields:
            try:
                status[field] = self.status_fields[field](torrent_id)
            except KeyError:
                pass
        return status

    def register_status_field(self, field, function):
        """Register a new status field.  This can be used in the same way the
        client requests other status information from core."""
        log.debug("Registering status field %s with PluginManager", field)
        self.status_fields[field] = function

    def deregister_status_field(self, field):
        """Deregisters a status field"""
        log.debug("Deregistering status field %s with PluginManager", field)
        try:
            del self.status_fields[field]
        except:
            log.warning("Unable to deregister status field %s", field)
