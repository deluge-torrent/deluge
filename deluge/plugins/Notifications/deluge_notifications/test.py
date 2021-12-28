# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2009-2010 UfSoft.org - Pedro Algarvio <pedro@algarvio.me>
#
# License: BSD - Please view the LICENSE file for additional information.
# ==============================================================================

import logging

from twisted.internet import task

from deluge import component
from deluge.event import DelugeEvent

log = logging.getLogger(__name__)


class FooEvent(DelugeEvent):
    """foo Event"""


class CustomEvent(DelugeEvent):
    """Just a custom event to test"""


class TestEmailNotifications(component.Component):
    def __init__(self, imp):
        component.Component.__init__(self, self.__class__.__name__, 5)
        self.__imp = imp
        self.lc = task.LoopingCall(self.update)
        self.n = 1
        self.events = [FooEvent(), CustomEvent()]
        self.events_classes = []

    def enable(self):
        log.debug('\n\nEnabling %s', self.__class__.__name__)
        for event in self.events:
            if self.__imp == 'core':
                # component.get('CorePlugin.Notifications').register_custom_email_notification(
                component.get('Notifications').register_custom_email_notification(
                    event.__class__.__name__, self.custom_email_message_provider
                )
            elif self.__imp == 'gtk':
                notifications_component = component.get('Notifications')
                notifications_component.register_custom_popup_notification(
                    event.__class__.__name__, self.custom_popup_message_provider
                )
                notifications_component.register_custom_blink_notification(
                    event.__class__.__name__, self.custom_blink_message_provider
                )
                notifications_component.register_custom_sound_notification(
                    event.__class__.__name__, self.custom_sound_message_provider
                )

        self.lc.start(60, False)

    def disable(self):
        log.debug('\n\nDisabling %s', self.__class__.__name__)
        self.lc.stop()

    def update(self):
        if self.__imp == 'core':
            log.debug('\n\nUpdating %s', self.__class__.__name__)
            self.events.append(self.events.pop(0))  # Re-Queue
            self.n += 1
            component.get('EventManager').emit(self.events[0])

    def custom_email_message_provider(self, *evt_args, **evt_kwargs):
        log.debug('Running custom email message provider: %s %s', evt_args, evt_kwargs)
        subject = f'{self.events[0].__class__.__name__} Email Subject: {self.n}'
        message = f'{self.events[0].__class__.__name__} Email Message: {self.n}'
        return subject, message

    def custom_popup_message_provider(self, *evt_args, **evt_kwargs):
        log.debug('Running custom popup message provider: %s %s', evt_args, evt_kwargs)
        title = f'{self.events[0].__class__.__name__} Popup Title: {self.n}'
        message = f'{self.events[0].__class__.__name__} Popup Message: {self.n}'
        return title, message

    def custom_blink_message_provider(self, *evt_args, **evt_kwargs):
        log.debug('Running custom blink message provider: %s %s', evt_args, evt_kwargs)
        return True

    def custom_sound_message_provider(self, *evt_args, **evt_kwargs):
        log.debug('Running custom sound message provider: %s %s', evt_args, evt_kwargs)
        return ''
