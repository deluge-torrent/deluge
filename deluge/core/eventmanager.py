# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component

log = logging.getLogger(__name__)


class EventManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, 'EventManager')
        self.handlers = {}

    def emit(self, event):
        """
        Emits the event to interested clients.

        :param event: DelugeEvent
        """
        # Emit the event to the interested clients
        component.get('RPCServer').emit_event(event)
        # Call any handlers for the event
        if event.name in self.handlers:
            for handler in self.handlers[event.name]:
                # log.debug('Running handler %s for event %s with args: %s', event.name, handler, event.args)
                try:
                    handler(*event.args)
                except Exception as ex:
                    log.error(
                        'Event handler %s failed in %s with exception %s',
                        event.name,
                        handler,
                        ex,
                    )

    def register_event_handler(self, event, handler):
        """
        Registers a function to be called when a `:param:event` is emitted.

        :param event: str, the event name
        :param handler: function, to be called when `:param:event` is emitted

        """
        if event not in self.handlers:
            self.handlers[event] = []

        if handler not in self.handlers[event]:
            self.handlers[event].append(handler)

    def deregister_event_handler(self, event, handler):
        """
        Deregisters an event handler function.

        :param event: str, the event name
        :param handler: function, currently registered to handle `:param:event`

        """
        if event in self.handlers and handler in self.handlers[event]:
            self.handlers[event].remove(handler)
