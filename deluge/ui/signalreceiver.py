#
# signalreceiver.py
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


import sys
import socket
import random

import gobject

from deluge.ui.client import aclient as client
import deluge.SimpleXMLRPCServer as SimpleXMLRPCServer
from SocketServer import ThreadingMixIn
import deluge.xmlrpclib as xmlrpclib
import threading
import socket

from deluge.log import LOG as log

class SignalReceiver(ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):

    def __init__(self):
        log.debug("SignalReceiver init..")
        # Set to true so that the receiver thread will exit

        self.signals = {}
        self.emitted_signals = []

        self.remote = False

        self.start_server()

    def start_server(self, port=None):
        # Setup the xmlrpc server
        host = "127.0.0.1"
        if self.remote:
            host = ""

        server_ready = False
        while not server_ready:
            if port:
                _port = port
            else:
                _port = random.randint(40000, 65535)
            try:
                SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(
                    self, (host, _port), logRequests=False, allow_none=True)
            except socket.error, e:
                log.debug("Trying again with another port: %s", e)
            except:
                log.error("Could not start SignalReceiver XMLRPC server: %s", e)
                sys.exit(0)
            else:
                self.port = _port
                server_ready = True

        # Register the emit_signal function
        self.register_function(self.emit_signal)

    def shutdown(self):
        """Shutdowns receiver thread"""
        log.debug("Shutting down signalreceiver")
        self._shutdown = True
        # De-register with the daemon so it doesn't try to send us more signals
        try:
            client.deregister_client()
            client.force_call()
        except Exception, e:
            log.debug("Unable to deregister client from server: %s", e)

        self.socket.shutdown(socket.SHUT_RDWR)
        log.debug("Joining listening thread..")
        self.listening_thread.join(1.0)
        return

    def set_remote(self, remote):
        self.remote = remote
        self.start_server(self.port)

    def run(self):
        """This gets called when we start the thread"""
        # Register the signal receiver with the core
        self._shutdown = False
        client.register_client(str(self.port))

        self.listening_thread = threading.Thread(target=self.handle_thread)

        gobject.timeout_add(50, self.handle_signals)

        try:
            self.listening_thread.start()
        except Exception, e:
            log.debug("Thread: %s", e)

    def handle_thread(self):
        try:
            while not self._shutdown:
                self.handle_request()
            self._shutdown = False
        except Exception, e:
            log.debug("handle_thread: %s", e)

    def get_port(self):
        """Get the port that the SignalReceiver is listening on"""
        return self.port

    def emit_signal(self, signal, *data):
        """Exported method used by the core to emit a signal to the client"""
        self.emitted_signals.append((signal, data))
        return

    def handle_signals(self):
        for signal, data in self.emitted_signals:
            try:
                for callback in self.signals[signal]:
                    gobject.idle_add(callback, *data)

            except Exception, e:
                log.warning("Unable to call callback for signal %s: %s", signal, e)

        self.emitted_signals = []
        return True

    def connect_to_signal(self, signal, callback):
        """Connect to a signal"""
        try:
            if callback not in self.signals[signal]:
                self.signals[signal].append(callback)
        except KeyError:
            self.signals[signal] = [callback]

