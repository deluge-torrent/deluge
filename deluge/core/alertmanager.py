#
# alertmanager.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
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
# 	Boston, MA    02110-1301, USA.
#


"""The AlertManager handles all the libtorrent alerts."""

import gobject

import deluge.component as component
try:
    import deluge.libtorrent as lt
except ImportError:
    import libtorrent as lt
    if not (libtorrent.version_major == 0 and libtorrent.version_minor == 14):
        raise ImportError("This version of Deluge requires libtorrent 0.14!")

from deluge.log import LOG as log

class AlertManager(component.Component):
    def __init__(self, session):
        log.debug("AlertManager initialized..")
        component.Component.__init__(self, "AlertManager", interval=50)
        self.session = session
        self.session.set_alert_mask(
            lt.alert.category_t.error_notification |
            lt.alert.category_t.port_mapping_notification |
            lt.alert.category_t.storage_notification |
            lt.alert.category_t.tracker_notification |
            lt.alert.category_t.status_notification |
            lt.alert.category_t.ip_block_notification)

        # handlers is a dictionary of lists {"alert_type": [handler1,h2,..]}
        self.handlers = {}

    def update(self):
        self.handle_alerts()

    def shutdown(self):
        del self.session
        del self.handlers

    def register_handler(self, alert_type, handler):
        """Registers a function that will be called when 'alert_type' is pop'd
        in handle_alerts.  The handler function should look like:
        handler(alert)
        Where 'alert' is the actual alert object from libtorrent
        """
        if alert_type not in self.handlers.keys():
            # There is no entry for this alert type yet, so lets make it with an
            # empty list.
            self.handlers[alert_type] = []

        # Append the handler to the list in the handlers dictionary
        self.handlers[alert_type].append(handler)
        log.debug("Registered handler for alert %s", alert_type)

    def deregister_handler(self, handler):
        """De-registers the 'handler' function from all alert types."""
        # Iterate through all handlers and remove 'handler' where found
        for (key, value) in self.handlers:
            if handler in value:
                # Handler is in this alert type list
                value.remove(handler)

    def handle_alerts(self, wait=False):
        """Pops all libtorrent alerts in the session queue and handles them
        appropriately."""
        alert = self.session.pop_alert()
        while alert is not None:
            # Loop through all alerts in the queue
            # Do some magic to get the alert type as a string
            alert_type = str(type(alert)).split("'")[1].split(".")[-1]
            # Display the alert message
            try:
                log.debug("%s: %s", alert_type, alert.message())
            except RuntimeError:
                log.debug("%s", alert_type)

            # Call any handlers for this alert type
            if alert_type in self.handlers.keys():
                for handler in self.handlers[alert_type]:
                    if not wait:
                        gobject.idle_add(handler, alert)
                    else:
                        handler(alert)

            alert = self.session.pop_alert()

        # Return True so that the timer continues
        return True
