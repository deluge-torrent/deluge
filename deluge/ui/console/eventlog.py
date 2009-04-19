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
# 	Boston, MA    02110-1301, USA.
#


import deluge.component as component
import deluge.common
from deluge.ui.client import client

from deluge.log import LOG as log

class EventLog(component.Component):
    """
    Prints out certain events as they are received from the core.
    """
    def __init__(self):
        component.Component.__init__(self, "EventLog")
        self.console = component.get("ConsoleUI")

        client.register_event_handler("TorrentAddedEvent", self.on_torrent_added_event)
        client.register_event_handler("PreTorrentRemovedEvent", self.on_torrent_removed_event)
        client.register_event_handler("TorrentStateChangedEvent", self.on_torrent_state_changed_event)
        client.register_event_handler("TorrentFinishedEvent", self.on_torrent_finished_event)
        client.register_event_handler("NewVersionAvailableEvent", self.on_new_version_available_event)
        client.register_event_handler("SessionPausedEvent", self.on_session_paused_event)
        client.register_event_handler("SessionResumedEvent", self.on_session_resumed_event)
        client.register_event_handler("ConfigValueChangedEvent", self.on_config_value_changed_event)

    def on_torrent_added_event(self, torrent_id):
        def on_torrent_status(status):
            self.console.write("{{event}}* TorrentAdded: {{info}}%s (%s)" % (status["name"], torrent_id))
        client.core.get_torrent_status(torrent_id, ["name"]).addCallback(on_torrent_status)

    def on_torrent_removed_event(self, torrent_id):
        self.console.write("{{event}}* TorrentRemovedEvent: {{info}}%s (%s)" %
            (self.console.get_torrent_name(torrent_id), torrent_id))

    def on_torrent_state_changed_event(self, torrent_id, state):
        log.debug("on_torrent_state_changed_event!")
        # Modify the state string color
        state_color = {
            "Seeding": "{{blue,black,bold}}",
            "Downloading": "{{green,black,bold}}",
            "Paused": "{{white,black}}",
            "Checking": "{{green,black}}",
            "Queued": "{{yellow,black}}",
            "Error": "{{red,black,bold}}"
        }
        if state in state_color:
            state = state_color[state] + state

        self.console.write("{{event}}* TorrentStateChanged: %s {{info}}%s (%s)" %
            (state, self.console.get_torrent_name(torrent_id), torrent_id))

    def on_torrent_paused_event(self, torrent_id):
        self.console.write("{{event}}* TorrentPaused: {{info}}%s (%s)" %
            (self.console.get_torrent_name(torrent_id), torrent_id))

    def on_torrent_finished_event(self, torrent_id):
        self.console.write("{{event}}* TorrentFinished: {{info}}%s (%s)" %
            (self.console.get_torrent_name(torrent_id), torrent_id))

    def on_new_version_available_event(self, version):
        self.console.write("{{event}}* NewVersionAvailable: {{info}}%s" %
            (version))

    def on_session_paused_event(self):
        self.console.write("{{event}}* SessionPaused")

    def on_session_resumed_event(self):
        self.console.write("{{event}}* SessionResumed")

    def on_config_value_changed_event(self, key, value):
        self.console.write("{{event}}* ConfigValueChanged: %s: %s" %
            (key, value))
