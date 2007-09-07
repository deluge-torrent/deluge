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
        # Handle the alerts every 50 milliseconds
        gobject.timeout_add(50, self.handle_alerts)
        
    def handle_alerts(self):
        """Pops all libtorrent alerts in the session queue and handles them
        appropriately."""
        alert = self.session.pop_alert()
        while alert is not None:
            # Loop through all alerts in the queue
            # Do some magic to the type string and display the alert message
            log.debug("%s: %s", str(type(alert)).split("'")[1].split(".")[2], 
                                                                    alert.msg())
            alert = self.session.pop_alert()

        # Return True so that the timer continues
        return True
