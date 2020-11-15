# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import hashlib
import logging
import os
import time

from twisted.internet.utils import getProcessOutputAndValue

import deluge.component as component
from deluge.common import windows_check
from deluge.configmanager import ConfigManager
from deluge.core.rpcserver import export
from deluge.event import DelugeEvent
from deluge.plugins.pluginbase import CorePluginBase

log = logging.getLogger(__name__)

DEFAULT_CONFIG = {'commands': []}

EXECUTE_ID = 0
EXECUTE_EVENT = 1
EXECUTE_COMMAND = 2

EVENT_MAP = {
    'complete': 'TorrentFinishedEvent',
    'added': 'TorrentAddedEvent',
    'removed': 'TorrentRemovedEvent',
}


class ExecuteCommandAddedEvent(DelugeEvent):
    """
    Emitted when a new command is added.
    """

    def __init__(self, command_id, event, command):
        self._args = [command_id, event, command]


class ExecuteCommandRemovedEvent(DelugeEvent):
    """
    Emitted when a command is removed.
    """

    def __init__(self, command_id):
        self._args = [command_id]


class Core(CorePluginBase):
    def enable(self):
        self.config = ConfigManager('execute.conf', DEFAULT_CONFIG)
        event_manager = component.get('EventManager')
        self.registered_events = {}
        self.preremoved_cache = {}

        # Go through the commands list and register event handlers
        for command in self.config['commands']:
            event = command[EXECUTE_EVENT]
            if event in self.registered_events:
                continue

            def create_event_handler(event):
                def event_handler(torrent_id, *arg):
                    self.execute_commands(torrent_id, event, *arg)

                return event_handler

            event_handler = create_event_handler(event)
            event_manager.register_event_handler(EVENT_MAP[event], event_handler)
            if event == 'removed':
                event_manager.register_event_handler(
                    'PreTorrentRemovedEvent', self.on_preremoved
                )
            self.registered_events[event] = event_handler

        log.debug('Execute core plugin enabled!')

    def on_preremoved(self, torrent_id):
        # Get and store the torrent info before it is removed
        torrent = component.get('TorrentManager').torrents[torrent_id]
        info = torrent.get_status(['name', 'download_location'])
        self.preremoved_cache[torrent_id] = [
            torrent_id,
            info['name'],
            info['download_location'],
        ]

    def execute_commands(self, torrent_id, event, *arg):
        if event == 'added' and arg[0]:
            # No futher action as from_state (arg[0]) is True
            return
        elif event == 'removed':
            torrent_id, torrent_name, download_location = self.preremoved_cache.pop(
                torrent_id
            )
        else:
            torrent = component.get('TorrentManager').torrents[torrent_id]
            info = torrent.get_status(['name', 'download_location'])
            # Grab the torrent name and download location
            # getProcessOutputAndValue requires args to be str
            torrent_name = info['name']
            download_location = info['download_location']

        log.debug('Running commands for %s', event)

        def log_error(result, command):
            (stdout, stderr, exit_code) = result
            if exit_code:
                log.warning('Command "%s" failed with exit code %d', command, exit_code)
                if stdout:
                    log.warning('stdout: %s', stdout)
                if stderr:
                    log.warning('stderr: %s', stderr)

        # Go through and execute all the commands
        for command in self.config['commands']:
            if command[EXECUTE_EVENT] == event:
                command = os.path.expandvars(command[EXECUTE_COMMAND])
                command = os.path.expanduser(command)

                cmd_args = [
                    torrent_id.encode('utf8'),
                    torrent_name.encode('utf8'),
                    download_location.encode('utf8'),
                ]
                if windows_check():
                    # Escape ampersand on windows (see #2784)
                    cmd_args = [cmd_arg.replace(b'&', b'^^^&') for cmd_arg in cmd_args]

                if os.path.isfile(command) and os.access(command, os.X_OK):
                    log.debug('Running %s with args: %s', command, cmd_args)
                    d = getProcessOutputAndValue(command, cmd_args, env=os.environ)
                    d.addCallback(log_error, command)
                else:
                    log.error('Execute script not found or not executable')

    def disable(self):
        self.config.save()
        event_manager = component.get('EventManager')
        for event, handler in self.registered_events.items():
            event_manager.deregister_event_handler(event, handler)
        log.debug('Execute core plugin disabled!')

    # Exported RPC methods #
    @export
    def add_command(self, event, command):
        command_id = hashlib.sha1(str(time.time()).encode()).hexdigest()
        self.config['commands'].append((command_id, event, command))
        self.config.save()
        component.get('EventManager').emit(
            ExecuteCommandAddedEvent(command_id, event, command)
        )

    @export
    def get_commands(self):
        return self.config['commands']

    @export
    def remove_command(self, command_id):
        for command in self.config['commands']:
            if command[EXECUTE_ID] == command_id:
                self.config['commands'].remove(command)
                component.get('EventManager').emit(
                    ExecuteCommandRemovedEvent(command_id)
                )
                break
        self.config.save()

    @export
    def save_command(self, command_id, event, cmd):
        for i, command in enumerate(self.config['commands']):
            if command[EXECUTE_ID] == command_id:
                self.config['commands'][i] = (command_id, event, cmd)
                break
        self.config.save()
