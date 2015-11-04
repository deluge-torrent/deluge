# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
import time

import deluge.component as component
from deluge.common import windows_check
from deluge.ui.client import client
from deluge.ui.console import colors

log = logging.getLogger(__name__)


class EventLog(component.Component):
    """
    Prints out certain events as they are received from the core.
    """
    def __init__(self):
        component.Component.__init__(self, "EventLog")
        self.console = component.get("ConsoleUI")
        self.prefix = "{!event!}* [%H:%M:%S] "
        self.date_change_format = "On {!yellow!}%a, %d %b %Y{!input!} %Z:"

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

        self.previous_time = time.localtime(0)

    def on_torrent_added_event(self, torrent_id, from_state):
        if from_state:
            return

        def on_torrent_status(status):
            self.write("{!green!}Torrent Added: {!info!}%s ({!cyan!}%s{!info!})" % (
                status["name"], torrent_id)
            )
            # Write out what state the added torrent took
            self.on_torrent_state_changed_event(torrent_id, status["state"])

        client.core.get_torrent_status(torrent_id, ["name", "state"]).addCallback(on_torrent_status)

    def on_torrent_removed_event(self, torrent_id):
        self.write("{!red!}Torrent Removed: {!info!}%s ({!cyan!}%s{!info!})" %
                   (self.console.get_torrent_name(torrent_id), torrent_id))

    def on_torrent_state_changed_event(self, torrent_id, state):
        # It's probably a new torrent, ignore it
        if not state:
            return
        # Modify the state string color
        if state in colors.state_color:
            state = colors.state_color[state] + state

        t_name = self.console.get_torrent_name(torrent_id)

        # Again, it's most likely a new torrent
        if not t_name:
            return

        self.write("%s: {!info!}%s ({!cyan!}%s{!info!})" %
                   (state, t_name, torrent_id))

    def on_torrent_finished_event(self, torrent_id):
        if not windows_check() and component.get("AllTorrents").config["ring_bell"]:
            import curses.beep
            curses.beep()
        self.write("{!info!}Torrent Finished: %s ({!cyan!}%s{!info!})" %
                   (self.console.get_torrent_name(torrent_id), torrent_id))

    def on_new_version_available_event(self, version):
        self.write("{!input!}New Deluge version available: {!info!}%s" %
                   (version))

    def on_session_paused_event(self):
        self.write("{!input!}Session Paused")

    def on_session_resumed_event(self):
        self.write("{!green!}Session Resumed")

    def on_config_value_changed_event(self, key, value):
        color = "{!white,black,bold!}"
        try:
            color = colors.type_color[type(value)]
        except KeyError:
            pass

        self.write("ConfigValueChanged: {!input!}%s: %s%s" % (key, color, value))

    def write(self, s):
        current_time = time.localtime()

        date_different = False
        for field in ["tm_mday", "tm_mon", "tm_year"]:
            c = getattr(current_time, field)
            p = getattr(self.previous_time, field)
            if c != p:
                date_different = True

        if date_different:
            string = time.strftime(self.date_change_format)
            self.console.write_event(" ")
            self.console.write_event(string)

        p = time.strftime(self.prefix)

        self.console.write_event(p + s)
        self.previous_time = current_time

    def on_plugin_enabled_event(self, name):
        self.write("PluginEnabled: {!info!}%s" % name)

    def on_plugin_disabled_event(self, name):
        self.write("PluginDisabled: {!info!}%s" % name)
