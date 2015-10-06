#
# alertmanager.py
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
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
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
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

"""

The AlertManager handles all the libtorrent alerts.

This should typically only be used by the Core.  Plugins should utilize the
`:mod:EventManager` for similar functionality.

"""

from twisted.internet import reactor

import deluge.component as component
from deluge._libtorrent import lt

from deluge.log import LOG as log

class AlertManager(component.Component):
    def __init__(self):
        log.debug("AlertManager initialized..")
        component.Component.__init__(self, "AlertManager", interval=0.3)
        self.session = component.get("Core").session

        self.session.set_alert_mask(
            lt.alert.category_t.error_notification |
            lt.alert.category_t.port_mapping_notification |
            lt.alert.category_t.storage_notification |
            lt.alert.category_t.tracker_notification |
            lt.alert.category_t.status_notification |
            lt.alert.category_t.ip_block_notification |
            lt.alert.category_t.performance_warning)

        # handlers is a dictionary of lists {"alert_type": [handler1,h2,..]}
        self.handlers = {}

        self.delayed_calls = []

    def update(self):
        self.delayed_calls = [dc for dc in self.delayed_calls if dc.active()]
        self.handle_alerts()

    def stop(self):
        for dc in self.delayed_calls:
            if dc.active():
                dc.cancel()
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
        log.debug("Registered handler for alert %s", alert_type)

    def deregister_handler(self, handler):
        """
        De-registers the `:param:handler` function from all alert types.

        :param handler: func, the handler function to deregister
        """
        # Iterate through all handlers and remove 'handler' where found
        for (key, value) in self.handlers.items():
            if handler in value:
                # Handler is in this alert type list
                value.remove(handler)

    def handle_alerts(self, wait=False):
        """
        Pops all libtorrent alerts in the session queue and handles them
        appropriately.

        :param wait: bool, if True then the handler functions will be run right
            away and waited to return before processing the next alert
        """
        alert = self.session.pop_alert()
        # Loop through all alerts in the queue
        while alert is not None:
            alert_type = type(alert).__name__
            # Display the alert message
            log.debug("%s: %s", alert_type, alert.message())
            # Call any handlers for this alert type
            if alert_type in self.handlers:
                for handler in self.handlers[alert_type]:
                    if not wait:
                        self.delayed_calls.append(reactor.callLater(0, handler, alert))
                    else:
                        handler(alert)

            alert = self.session.pop_alert()
