#
# eventlog.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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


import deluge.component as component
import deluge.common
import colors
from deluge.ui.client import client

from deluge.log import LOG as log

class EventLog(component.Component):
    """
    Prints out certain events as they are received from the core.
    """
    def __init__(self):
        component.Component.__init__(self, "EventLog")
        self.console = component.get("ConsoleUI")
        self.prefix = "{!event!}* "

        client.register_event_handler("TorrentAddedEvent", self.on_torrent_added_event)
        client.register_event_handler("PreTorrentRemovedEvent", self.on_torrent_removed_event)
        client.register_event_handler("TorrentStateChangedEvent", self.on_torrent_state_changed_event)
        client.register_event_handler("TorrentFinishedEvent", self.on_torrent_finished_event)
        client.register_event_handler("NewVersionAvailableEvent", self.on_new_version_available_event)
        client.register_event_handler("SessionPausedEvent", self.on_session_paused_event)
        client.register_event_handler("SessionResumedEvent", self.on_session_resumed_event)
        client.register_event_handler("ConfigValueChangedEvent", self.on_config_value_changed_event)
        client.register_event_handler("PluginEnabledEvent", self.on_plugin_enabled_event)
        client.register_event_handler("PluginDisabledEvent", self.on_plugin_disabled_event)

    def on_torrent_added_event(self, torrent_id):
        def on_torrent_status(status):
            self.console.write(self.prefix + "TorrentAdded: {!info!}%s (%s)" % (status["name"], torrent_id))
        client.core.get_torrent_status(torrent_id, ["name"]).addCallback(on_torrent_status)

    def on_torrent_removed_event(self, torrent_id):
        self.console.write(self.prefix + "TorrentRemoved: {!info!}%s (%s)" %
            (self.console.get_torrent_name(torrent_id), torrent_id))

    def on_torrent_state_changed_event(self, torrent_id, state):
        # Modify the state string color
        if state in colors.state_color:
            state = colors.state_color[state] + state

        self.console.write(self.prefix + "TorrentStateChanged: %s {!info!}%s (%s)" %
            (state, self.console.get_torrent_name(torrent_id), torrent_id))

    def on_torrent_paused_event(self, torrent_id):
        self.console.write(self.prefix + "TorrentPaused: {!info!}%s (%s)" %
            (self.console.get_torrent_name(torrent_id), torrent_id))

    def on_torrent_finished_event(self, torrent_id):
        self.console.write(self.prefix + "TorrentFinished: {!info!}%s (%s)" %
            (self.console.get_torrent_name(torrent_id), torrent_id))

    def on_new_version_available_event(self, version):
        self.console.write(self.prefix + "NewVersionAvailable: {!info!}%s" %
            (version))

    def on_session_paused_event(self):
        self.console.write(self.prefix + "SessionPaused")

    def on_session_resumed_event(self):
        self.console.write(self.prefix + "SessionResumed")

    def on_config_value_changed_event(self, key, value):
        color = "{!white,black,bold!}"
        if type(value) in colors.type_color:
            color = colors.type_color[type(value)]

        self.console.write(self.prefix + "ConfigValueChanged: {!input!}%s: %s%s" %
            (key, color, value))

    def on_plugin_enabled_event(self, name):
        self.console.write(self.prefix + "PluginEnabled: {!info!}%s" % name)

    def on_plugin_disabled_event(self, name):
        self.console.write(self.prefix + "PluginDisabled: {!info!}%s" % name)
