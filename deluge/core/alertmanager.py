#
# alertmanager.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.

"""The AlertManager handles all the libtorrent alerts."""

import gobject

import deluge.libtorrent as lt
from deluge.log import LOG as log

class AlertManager:
    def __init__(self, session):
        log.debug("AlertManager initialized..")
        self.session = session
        self.session.set_severity_level(lt.alert.severity_levels.info)
        # handlers is a dictionary of lists {"alert_type": [handler1,h2,..]}
        self.handlers = {}
        # Handle the alerts every 50 milliseconds
        gobject.timeout_add(50, self.handle_alerts)
    
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
        log.debug("Registered handler %s for alert %s", handler, alert_type)
    
    def deregister_handler(self, handler):
        """De-registers the 'handler' function from all alert types."""
        # Iterate through all handlers and remove 'handler' where found
        for (key, value) in self.handlers:
            if handler in value:
                # Handler is in this alert type list
                value.remove(handler)
                    
    def handle_alerts(self):
        """Pops all libtorrent alerts in the session queue and handles them
        appropriately."""
        alert = self.session.pop_alert()
        while alert is not None:
            # Loop through all alerts in the queue
            # Do some magic to get the alert type as a string
            alert_type = str(type(alert)).split("'")[1].split(".")[2]
            # Display the alert message
            log.debug("%s: %s", alert_type, alert.msg())
            # Call any handlers for this alert type
            if alert_type in self.handlers.keys():
                for handler in self.handlers[alert_type]:
                    handler(alert)
                    
            alert = self.session.pop_alert()

        # Return True so that the timer continues
        return True
