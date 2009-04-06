#
# signalmanager.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
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

#


import deluge.xmlrpclib as xmlrpclib
import socket
import struct

import gobject

import deluge.component as component
from deluge.log import LOG as log

class Transport(xmlrpclib.Transport):
    def make_connection(self, host):
        # create a HTTP connection object from a host descriptor
        import httplib
        host, extra_headers, x509 = self.get_host_info(host)
        h = httplib.HTTP(host)
        h._conn.connect()
        h._conn.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                      struct.pack('ii', 1, 0))
        return h

class SignalManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, "SignalManager")
        self.clients = {}
        self.handlers = {}

    def shutdown(self):
        self.clients = {}
        self.handlers = {}

    def register_handler(self, signal, handler):
        """Registers a handler for signals"""
        if signal not in self.handler.keys():
            self.handler[signal] = []

        self.handler[signal].append(handler)
        log.debug("Registered signal handler for %s", signal)

    def deregister_handler(self, handler):
        """De-registers the 'handler' function from all signal types."""
        # Iterate through all handlers and remove 'handler' where found
        for (key, value) in self.handlers:
            if handler in value:
                value.remove(handler)

    def deregister_client(self, address):
        """Deregisters a client"""
        log.debug("Deregistering %s as a signal reciever..", address)
        for client in self.clients.keys():
            if client.split("//")[1].split(":")[0] == address:
                del self.clients[client]
                break

    def register_client(self, address, port):
        """Registers a client to emit signals to."""
        uri = "http://" + str(address) + ":" + str(port)
        log.debug("Registering %s as a signal reciever..", uri)
        self.clients[uri] = xmlrpclib.ServerProxy(uri, transport=Transport())
        #self.clients[uri].socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                    #  struct.pack('ii', 1, 0))

    def emit(self, signal, *data):
        # Run the handlers
        if signal in self.handlers.keys():
            for handler in self.handlers[signal]:
                handler(*data)

        for uri in self.clients:
            gobject.idle_add(self._emit, uri, signal, 1, *data)

    def _emit(self, uri, signal, count, *data):
        if uri not in self.clients:
            return
        client = self.clients[uri]
        try:
            client.emit_signal(signal, *data)
        except (socket.error, Exception), e:
            log.warning("Unable to emit signal to client %s: %s (%d)", client, e, count)
            if count < 30:
                gobject.timeout_add(1000, self._emit, uri, signal, count + 1, *data)
            else:
                log.info("Removing %s because it couldn't be reached..", uri)
                del self.clients[uri]
