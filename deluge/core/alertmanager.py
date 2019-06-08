# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""

The AlertManager handles all the libtorrent alerts.

This should typically only be used by the Core. Plugins should utilize the
`:mod:EventManager` for similar functionality.

"""
from __future__ import unicode_literals

import logging
import types

from twisted.internet import reactor

import deluge.component as component
from deluge._libtorrent import lt
from deluge.common import decode_bytes

log = logging.getLogger(__name__)

try:
    SimpleNamespace = types.SimpleNamespace  # Python 3.3+
except AttributeError:

    class SimpleNamespace(object):  # Python 2.7
        def __init__(self, **attr):
            self.__dict__.update(attr)


class AlertManager(component.Component):
    """AlertManager fetches and processes libtorrent alerts"""

    def __init__(self):
        log.debug('AlertManager init...')
        component.Component.__init__(self, 'AlertManager', interval=0.3)
        self.session = component.get('Core').session

        # Increase the alert queue size so that alerts don't get lost.
        self.alert_queue_size = 10000
        self.set_alert_queue_size(self.alert_queue_size)

        alert_mask = (
            lt.alert.category_t.error_notification
            | lt.alert.category_t.port_mapping_notification
            | lt.alert.category_t.storage_notification
            | lt.alert.category_t.tracker_notification
            | lt.alert.category_t.status_notification
            | lt.alert.category_t.ip_block_notification
            | lt.alert.category_t.performance_warning
        )

        self.session.apply_settings({'alert_mask': alert_mask})

        # handlers is a dictionary of lists {"alert_type": [handler1,h2,..]}
        self.handlers = {}
        self.delayed_calls = []

    def update(self):
        self.delayed_calls = [dc for dc in self.delayed_calls if dc.active()]
        self.handle_alerts()

    def stop(self):
        for delayed_call in self.delayed_calls:
            if delayed_call.active():
                delayed_call.cancel()
        self.delayed_calls = []

    def register_handler(self, alert_type, handler):
        """
        Registers a function that will be called when 'alert_type' is pop'd
        in handle_alerts.  The handler function should look like: handler(alert)
        Where 'alert' is the actual alert object from libtorrent.

        :param alert_type: str, this is string representation of the alert name
        :param handler: func(alert), the function to be called when the alert is raised
        """
        if alert_type not in self.handlers:
            # There is no entry for this alert type yet, so lets make it with an
            # empty list.
            self.handlers[alert_type] = []

        # Append the handler to the list in the handlers dictionary
        self.handlers[alert_type].append(handler)
        log.debug('Registered handler for alert %s', alert_type)

    def deregister_handler(self, handler):
        """
        De-registers the `:param:handler` function from all alert types.

        :param handler: func, the handler function to deregister
        """
        # Iterate through all handlers and remove 'handler' where found
        for (dummy_key, value) in self.handlers.items():
            if handler in value:
                # Handler is in this alert type list
                value.remove(handler)

    def handle_alerts(self):
        """
        Pops all libtorrent alerts in the session queue and handles them appropriately.
        """
        alerts = self.session.pop_alerts()
        if not alerts:
            return

        num_alerts = len(alerts)
        if log.isEnabledFor(logging.DEBUG):
            log.debug('Alerts queued: %s', num_alerts)
        if num_alerts > 0.9 * self.alert_queue_size:
            log.warning(
                'Warning total alerts queued, %s, passes 90%% of queue size.',
                num_alerts,
            )

        # Loop through all alerts in the queue
        for alert in alerts:
            alert_type = type(alert).__name__
            # Display the alert message
            if log.isEnabledFor(logging.DEBUG):
                log.debug('%s: %s', alert_type, decode_bytes(alert.message()))
            # Call any handlers for this alert type
            if alert_type in self.handlers:
                for handler in self.handlers[alert_type]:
                    if log.isEnabledFor(logging.DEBUG):
                        log.debug('Handling alert: %s', alert_type)
                    # Copy alert attributes
                    alert_copy = SimpleNamespace(
                        **{
                            attr: getattr(alert, attr)
                            for attr in dir(alert)
                            if not attr.startswith('__')
                        }
                    )
                    self.delayed_calls.append(reactor.callLater(0, handler, alert_copy))

    def set_alert_queue_size(self, queue_size):
        """Sets the maximum size of the libtorrent alert queue"""
        log.info('Alert Queue Size set to %s', queue_size)
        self.alert_queue_size = queue_size
        component.get('Core').apply_session_setting(
            'alert_queue_size', self.alert_queue_size
        )
