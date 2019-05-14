# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Pedro Algarvio <pedro@algarvio.me>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os.path

from pkg_resources import resource_filename
from twisted.internet import defer

from deluge import component
from deluge.event import known_events

log = logging.getLogger(__name__)


def get_resource(filename):
    return resource_filename(__package__, os.path.join('data', filename))


class CustomNotifications(object):
    def __init__(self, plugin_name=None):
        self.custom_notifications = {'email': {}, 'popup': {}, 'blink': {}, 'sound': {}}

    def enable(self):
        pass

    def disable(self):
        for kind in self.custom_notifications:
            for eventtype in list(self.custom_notifications[kind]):
                wrapper, handler = self.custom_notifications[kind][eventtype]
                self._deregister_custom_provider(kind, eventtype)

    def _handle_custom_providers(self, kind, eventtype, *args, **kwargs):
        log.debug(
            'Calling CORE custom %s providers for %s: %s %s',
            kind,
            eventtype,
            args,
            kwargs,
        )
        if eventtype in self.config['subscriptions'][kind]:
            wrapper, handler = self.custom_notifications[kind][eventtype]
            log.debug('Found handler for kind %s: %s', kind, handler)
            custom_notif_func = getattr(self, 'handle_custom_%s_notification' % kind)
            d = defer.maybeDeferred(handler, *args, **kwargs)
            d.addCallback(custom_notif_func, eventtype)
            d.addCallback(self._on_notify_sucess, kind)
            d.addErrback(self._on_notify_failure, kind)
            return d

    def _register_custom_provider(self, kind, eventtype, handler):
        if not self._handled_eventtype(eventtype, handler):
            return defer.succeed('Event not handled')
        if eventtype not in self.custom_notifications:

            def wrapper(*args, **kwargs):
                return self._handle_custom_providers(kind, eventtype, *args, **kwargs)

            self.custom_notifications[kind][eventtype] = (wrapper, handler)
        else:
            wrapper, handler = self.custom_notifications[kind][eventtype]
        try:
            component.get('EventManager').register_event_handler(eventtype, wrapper)
        except KeyError:
            from deluge.ui.client import client

            client.register_event_handler(eventtype, wrapper)

    def _deregister_custom_provider(self, kind, eventtype):
        try:
            wrapper, handler = self.custom_notifications[kind][eventtype]
            try:
                component.get('EventManager').deregister_event_handler(
                    eventtype, wrapper
                )
            except KeyError:
                from deluge.ui.client import client

                client.deregister_event_handler(eventtype, wrapper)
            self.custom_notifications[kind].pop(eventtype)
        except KeyError:
            pass

    def _handled_eventtype(self, eventtype, handler):
        if eventtype not in known_events:
            log.error('The event "%s" is not known', eventtype)
            return False
        if known_events[eventtype].__module__.startswith('deluge.event'):
            if handler.__self__ is self:
                return True
            log.error(
                'You cannot register custom notification providers '
                'for built-in event types.'
            )
            return False
        return True

    def _on_notify_sucess(self, result, kind):
        log.debug('Notification success using %s: %s', kind, result)
        return result

    def _on_notify_failure(self, failure, kind):
        log.debug('Notification failure using %s: %s', kind, failure)
        return failure
