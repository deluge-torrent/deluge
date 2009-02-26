#
# eventmanager.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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

import deluge.component as component
from deluge.log import LOG as log

class EventManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, "EventManager")
        self.handlers = {}

    def emit(self, event):
        """
        Emits the event to interested clients.

        :param event: DelugeEvent
        """
        # Emit the event to the interested clients
        component.get("RPCServer").emit_event(event)
        # Call any handlers for the event
        if event.name in self.handlers:
            for handler in self.handlers[event.name]:
                #log.debug("Running handler %s for event %s with args: %s", event.name, handler, event.args)
                handler(*event.args)

    def register_event_handler(self, event, handler):
        """
        Registers a function to be called when a `:param:event` is emitted.

        :param event: str, the event name
        :param handler: function, to be called when `:param:event` is emitted

        """
        if event not in self.handlers:
            self.handlers[event] = []

        if handler not in self.handlers[event]:
            self.handlers[event].append(handler)

    def deregister_event_handler(self, event, handler):
        """
        Deregisters an event handler function.

        :param event: str, the event name
        :param handler: function, currently registered to handle `:param:event`

        """
        if event in self.handlers and handler in self.handlers[event]:
            self.handlers[event].remove(handler)
