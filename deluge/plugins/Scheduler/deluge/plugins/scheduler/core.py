# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import time

from twisted.internet import reactor

import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from deluge.event import DelugeEvent
from deluge.plugins.pluginbase import CorePluginBase

log = logging.getLogger(__name__)

DEFAULT_PREFS = {
    'low_down': -1.0,
    'low_up': -1.0,
    'low_active': -1,
    'low_active_down': -1,
    'low_active_up': -1,
    'button_state': [[0] * 7 for dummy in range(24)],
}

STATES = {0: 'Green', 1: 'Yellow', 2: 'Red'}

CONTROLLED_SETTINGS = [
    'max_download_speed',
    'max_upload_speed',
    'max_active_limit',
    'max_active_downloading',
    'max_active_seeding',
]


class SchedulerEvent(DelugeEvent):
    """
    Emitted when a schedule state changes.
    """

    def __init__(self, colour):
        """
        :param colour: str, the current scheduler state
        """
        self._args = [colour]


class Core(CorePluginBase):
    def enable(self):
        # Create the defaults with the core config
        core_config = component.get('Core').config
        DEFAULT_PREFS['low_down'] = core_config['max_download_speed']
        DEFAULT_PREFS['low_up'] = core_config['max_upload_speed']
        DEFAULT_PREFS['low_active'] = core_config['max_active_limit']
        DEFAULT_PREFS['low_active_down'] = core_config['max_active_downloading']
        DEFAULT_PREFS['low_active_up'] = core_config['max_active_seeding']

        self.config = deluge.configmanager.ConfigManager(
            'scheduler.conf', DEFAULT_PREFS
        )

        self.state = self.get_state()

        # Apply the scheduling rules
        self.do_schedule(False)

        # Schedule the next do_schedule() call for on the next hour
        now = time.localtime(time.time())
        secs_to_next_hour = ((60 - now[4]) * 60) + (60 - now[5])
        self.timer = reactor.callLater(secs_to_next_hour, self.do_schedule)

        # Register for config changes so state isn't overridden
        component.get('EventManager').register_event_handler(
            'ConfigValueChangedEvent', self.on_config_value_changed
        )

    def disable(self):
        if self.timer.active():
            self.timer.cancel()
        component.get('EventManager').deregister_event_handler(
            'ConfigValueChangedEvent', self.on_config_value_changed
        )
        self.__apply_set_functions()

    def update(self):
        pass

    def on_config_value_changed(self, key, value):
        if key in CONTROLLED_SETTINGS:
            self.do_schedule(False)

    def __apply_set_functions(self):
        """
        Have the core apply it's bandwidth settings as specified in core.conf.
        """
        core_config = deluge.configmanager.ConfigManager('core.conf')
        for setting in CONTROLLED_SETTINGS:
            component.get('PreferencesManager').do_config_set_func(
                setting, core_config[setting]
            )
        # Resume the session if necessary
        component.get('Core').resume_session()

    def do_schedule(self, timer=True):
        """
        This is where we apply schedule rules.
        """

        state = self.get_state()

        if state == 'Green':
            # This is Green (Normal) so we just make sure we've applied the
            # global defaults
            self.__apply_set_functions()
        elif state == 'Yellow':
            # This is Yellow (Slow), so use the settings provided from the user
            settings = {
                'active_limit': self.config['low_active'],
                'active_downloads': self.config['low_active_down'],
                'active_seeds': self.config['low_active_up'],
                'download_rate_limit': int(self.config['low_down'] * 1024),
                'upload_rate_limit': int(self.config['low_up'] * 1024),
            }
            component.get('Core').apply_session_settings(settings)
            # Resume the session if necessary
            component.get('Core').resume_session()
        elif state == 'Red':
            # This is Red (Stop), so pause the libtorrent session
            component.get('Core').pause_session()

        if state != self.state:
            # The state has changed since last update so we need to emit an event
            self.state = state
            component.get('EventManager').emit(SchedulerEvent(self.state))

        if timer:
            # Call this again in 1 hour
            self.timer = reactor.callLater(3600, self.do_schedule)

    @export()
    def set_config(self, config):
        """Sets the config dictionary."""
        for key in config:
            self.config[key] = config[key]
        self.config.save()
        self.do_schedule(False)

    @export()
    def get_config(self):
        """Returns the config dictionary."""
        return self.config.config

    @export()
    def get_state(self):
        now = time.localtime(time.time())
        level = self.config['button_state'][now[3]][now[6]]
        return STATES[level]
