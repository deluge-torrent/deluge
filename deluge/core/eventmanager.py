# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

from twisted.internet import reactor

import deluge.component as component

log = logging.getLogger(__name__)


class EventManagerBase(object):
    def __init__(self):
        self.event_handlers = {}

    def emit(self, event):
        """
        Emits the event to interested clients.

        :param event: DelugeEvent
        """
        self.pre_emit(event)
        self.handle_event(event)

    def handle_event(self, event):
        # Call any event_handlers for the event
        if event.name in self.event_handlers:
            for handler in self.event_handlers[event.name]:
                # log.debug("Running handler %s for event %s with args: %s", event.name, handler, event.args)
                try:
                    self.call_handler(handler, event.args)
                except Exception as ex:
                    log.error('Event handler %s failed in %s with exception %s', event.name, handler, ex)

    def pre_emit(self, event):
        pass

    def call_handler(self, handler, args):
        handler(*args)

    def register_event_handler(self, event, handler):
        """
        Registers a function to be called when a `:param:event` is emitted.

        :param event: str, the event name
        :param handler: function, to be called when `:param:event` is emitted

        """
        if event not in self.event_handlers:
            self.event_handlers[event] = []

        if handler not in self.event_handlers[event]:
            self.event_handlers[event].append(handler)

    def deregister_event_handler(self, event, handler):
        """
        Deregisters an event handler function.

        :param event: str, the event name
        :param handler: function, currently registered to handle `:param:event`

        """
        if event in self.event_handlers and handler in self.event_handlers[event]:
            self.event_handlers[event].remove(handler)

    def has_handler(self, event):
        return event in self.event_handlers


class EventManager(EventManagerBase, component.Component):
    def __init__(self):
        EventManagerBase.__init__(self)
        component.Component.__init__(self, 'EventManager')

    def pre_emit(self, event):
        component.get('RPCServer').emit_event(event)


class EventManagerClient(EventManagerBase):
    def __init__(self):
        super(EventManagerClient, self).__init__()

    def copy(self):
        cp = EventManagerClient()
        cp.event_handlers = dict(self.event_handlers)
        return cp

    def call_handler(self, handler, args):
        reactor.callLater(0, handler, *args)
