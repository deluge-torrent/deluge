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
import threading
import time
from collections import defaultdict
from functools import partial
from typing import Any, Callable

from twisted.internet import reactor, task, threads

import deluge.component as component
from deluge._libtorrent import lt
from deluge.common import decode_bytes

log = logging.getLogger(__name__)


class AlertManager(component.Component):
    """AlertManager fetches and processes libtorrent alerts"""

    def __init__(self):
        log.debug('AlertManager init...')
        component.Component.__init__(self, 'AlertManager')
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
        self.handlers_timeout_secs = 2
        self.delayed_calls = []
        self._event = threading.Event()

    def update(self):
        pass

    def start(self):
        thread = threading.Thread(
            target=self.wait_for_alert_in_thread, name='alert-poller', daemon=True
        )
        thread.start()
        self._event.set()

    def stop(self):
        self.cancel_delayed_calls()

    def pause(self):
        self._event.clear()

    def resume(self):
        self._event.set()

    def wait_for_alert_in_thread(self):
        while self._component_state not in ('Stopping', 'Stopped'):
            if self.check_delayed_calls():
                time.sleep(0.05)
                continue

            if self.session.wait_for_alert(1000) is None:
                continue
            if self._event.wait():
                threads.blockingCallFromThread(reactor, self.maybe_handle_alerts)

    def on_delayed_call_timeout(self, result, timeout, **kwargs):
        log.warning('Alert handler was timed-out before being called %s', kwargs)

    def cancel_delayed_calls(self):
        """Cancel all delayed handlers."""
        for delayed_call in self.delayed_calls:
            delayed_call.cancel()
        self.delayed_calls = []

    def check_delayed_calls(self) -> bool:
        """Returns True if any handler calls are delayed."""
        self.delayed_calls = [dc for dc in self.delayed_calls if not dc.called]
        return len(self.delayed_calls) > 0

    def maybe_handle_alerts(self) -> None:
        if self._component_state != 'Started':
            return

        self.handle_alerts()

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
                d = task.deferLater(reactor, 0, handler, alert)
                on_handler_timeout = partial(
                    self.on_delayed_call_timeout,
                    handler=handler.__qualname__,
                    alert_type=alert_type,
                )
                d.addTimeout(
                    self.handlers_timeout_secs,
                    reactor,
                    onTimeoutCancel=on_handler_timeout,
                )
                self.delayed_calls.append(d)

    def set_alert_queue_size(self, queue_size):
        """Sets the maximum size of the libtorrent alert queue"""
        log.info('Alert Queue Size set to %s', queue_size)
        self.alert_queue_size = queue_size
        component.get('Core').apply_session_setting(
            'alert_queue_size', self.alert_queue_size
        )
