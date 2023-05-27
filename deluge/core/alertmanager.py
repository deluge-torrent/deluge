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
import contextlib
import logging
from collections import defaultdict
from types import SimpleNamespace
from typing import Any, Callable

from twisted.internet import reactor

import deluge.component as component
from deluge._libtorrent import lt
from deluge.common import decode_bytes

log = logging.getLogger(__name__)


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
            | lt.alert.category_t.file_progress_notification
        )

        self.session.apply_settings({'alert_mask': alert_mask})

        # handlers is a dictionary of lists {"alert_type": [handler1,h2,..]}
        self.handlers = defaultdict(list)
        self.delayed_calls = []

    def update(self):
        self.delayed_calls = [dc for dc in self.delayed_calls if dc.active()]
        self.handle_alerts()

    def stop(self):
        for delayed_call in self.delayed_calls:
            if delayed_call.active():
                delayed_call.cancel()
        self.delayed_calls = []

    def register_handler(self, alert_type: str, handler: Callable[[Any], None]) -> None:
        """
        Registers a function that will be called when 'alert_type' is pop'd
        in handle_alerts.  The handler function should look like: handler(alert)
        Where 'alert' is the actual alert object from libtorrent.

        Args:
            alert_type: String representation of the libtorrent alert name.
                Can be supplied with or without `_alert` suffix.
            handler: Callback function when the alert is raised.
        """
        if alert_type and alert_type.endswith('_alert'):
            alert_type = alert_type[: -len('_alert')]

        self.handlers[alert_type].append(handler)
        log.debug('Registered handler for alert %s', alert_type)

    def deregister_handler(self, handler: Callable[[Any], None]):
        """
        De-registers the `handler` function from all alert types.

        Args:
            handler: The handler function to deregister.
        """
        for alert_type_handlers in self.handlers.values():
            with contextlib.suppress(ValueError):
                alert_type_handlers.remove(handler)

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

        for alert in alerts:
            alert_type = alert.what()

            # Display the alert message
            if log.isEnabledFor(logging.DEBUG):
                log.debug('%s: %s', alert_type, decode_bytes(alert.message()))

            if alert_type not in self.handlers:
                continue

            # Call any handlers for this alert type
            for handler in self.handlers[alert_type]:
                if log.isEnabledFor(logging.DEBUG):
                    log.debug('Handling alert: %s', alert_type)

                alert_copy = self.create_alert_copy(alert)
                self.delayed_calls.append(reactor.callLater(0, handler, alert_copy))

    @staticmethod
    def create_alert_copy(alert):
        """Create a Python copy of libtorrent alert

        Avoid segfault if an alert is handled after next pop_alert call"""
        return SimpleNamespace(
            **{
                attr: getattr(alert, attr)
                for attr in dir(alert)
                if not attr.startswith('__')
            }
        )

    def set_alert_queue_size(self, queue_size):
        """Sets the maximum size of the libtorrent alert queue"""
        log.info('Alert Queue Size set to %s', queue_size)
        self.alert_queue_size = queue_size
        component.get('Core').apply_session_setting(
            'alert_queue_size', self.alert_queue_size
        )
