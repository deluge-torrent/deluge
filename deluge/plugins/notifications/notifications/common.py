#
# common.py
#
# Copyright (C) 2009 Pedro Algarvio <ufs@ufsoft.org>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

from twisted.internet import defer
from deluge import component
from deluge.log import LOG as log

try:
    from deluge.event import known_events
except ImportError:
    # Old deluge version
    known_events = {}


def get_resource(filename):
    import pkg_resources, os
    return pkg_resources.resource_filename("notifications",
                                           os.path.join("data", filename))


class CustomNotifications(object):
    config = None   # shut-up pylint

    def __init__(self, plugin_name=None):
        self.custom_notifications = {
            "email": {},
            "popup": {},
            "blink": {},
            "sound": {}
        }

    def enable(self):
        pass

    def disable(self):
        for kind in self.custom_notifications.iterkeys():
            for eventtype in self.custom_notifications[kind].copy().iterkeys():
                wrapper, handler = self.custom_notifications[kind][eventtype]
                self._deregister_custom_provider(kind, eventtype)

    def _handle_custom_providers(self, kind, eventtype, *args, **kwargs):
        log.debug("Calling CORE's custom %s providers for %s: %s %s",
                  kind, eventtype, args, kwargs)
        if eventtype in self.config["subscriptions"][kind]:
            wrapper, handler = self.custom_notifications[kind][eventtype]
            log.debug("Found handler for kind %s: %s", kind, handler)
            custom_notif_func = getattr(self,
                                        'handle_custom_%s_notification' % kind)
            d = defer.maybeDeferred(handler, *args, **kwargs)
            d.addCallback(custom_notif_func, eventtype)
            d.addCallback(self._on_notify_sucess, kind)
            d.addErrback(self._on_notify_failure, kind)
            return d

    def _register_custom_provider(self, kind, eventtype, handler):
        if not self._handled_eventtype(eventtype, handler):
            return defer.succeed("Event not handled")
        if eventtype not in self.custom_notifications:
            def wrapper(*args, **kwargs):
                return self._handle_custom_providers(kind, eventtype,
                                                      *args, **kwargs)
            self.custom_notifications[kind][eventtype] = (wrapper, handler)
        else:
            wrapper, handler = self.custom_notifications[kind][eventtype]
        try:
            component.get("EventManager").register_event_handler(
                eventtype, wrapper
            )
        except KeyError:
            from deluge.ui.client import client
            client.register_event_handler(eventtype, wrapper)

    def _deregister_custom_provider(self, kind, eventtype):
        try:
            wrapper, handler = self.custom_notifications[kind][eventtype]
            try:
                component.get("EventManager").deregister_event_handler(
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
            log.error("The event \"%s\" is not known" % eventtype)
            return False
        if known_events[eventtype].__module__.startswith('deluge.event'):
            if handler.im_self is self:
                return True
            log.error("You cannot register custom notification providers "
                      "for built-in event types.")
            return False
        return True

    def _on_notify_sucess(self, result, kind):
        log.debug("Notification success using %s: %s", kind, result)
        return result

    def _on_notify_failure(self, failure, kind):
        log.debug("Notification failure using %s: %s", kind, failure)
        return failure

