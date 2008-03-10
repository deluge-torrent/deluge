#
# signalreceiver.py
#
# Copyright (C) 2007, 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
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

import sys
import socket
import random

import gobject

from deluge.ui.client import aclient as client
import deluge.SimpleXMLRPCServer as SimpleXMLRPCServer
from SocketServer import ThreadingMixIn
import deluge.xmlrpclib as xmlrpclib
import threading

from deluge.log import LOG as log

class SignalReceiver(
        ThreadingMixIn, 
        SimpleXMLRPCServer.SimpleXMLRPCServer):
    
    def __init__(self):
        log.debug("SignalReceiver init..")
        gobject.threads_init()
    
        # Set to true so that the receiver thread will exit
        self._shutdown = False

        self.signals = {}
    
        self.remote = False

        
    def shutdown(self):
        """Shutdowns receiver thread"""
        self._shutdown = True
        # De-register with the daemon so it doesn't try to send us more signals
        try:
            client.deregister_client()
            client.force_call()
        except:
            pass
        log.debug("Shutting down signalreceiver")

        # Hacky.. sends a request to our local receiver to ensure that it
        # shutdowns.. This is because handle_request() is a blocking call.
        receiver = xmlrpclib.ServerProxy("http://localhost:" + str(self.port),
            allow_none=True)
        try:
            receiver.emit_signal("shutdown", None)
        except:
            # We don't care about errors at this point
            pass
    
    def set_remote(self, remote):
        self.remote = remote
            
    def run(self):
        """This gets called when we start the thread"""
        host = "localhost"
        if self.remote == True:
            host = ""
            
        # Setup the xmlrpc server
        server_ready = False
        while not server_ready:
            port = random.randint(40000, 65535)
            try:
                SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(
                    self, (host, port), logRequests=False, allow_none=True)
            except socket.error, e:
                log.debug("Trying again with another port: %s", e)
            except:
                log.error("Could not start SignalReceiver XMLRPC server: %s", e)
                sys.exit(0)
            else:
                self.port = port
                server_ready = True
            
        # Register the emit_signal function
        self.register_function(self.emit_signal)
        
        # Register the signal receiver with the core
        client.register_client(str(self.port))
        
        t = threading.Thread(target=self.handle_thread)
        t.start()
    
    def handle_thread(self):
        while not self._shutdown:
            self.handle_request()
        self._shutdown = False
            
    def emit_signal(self, signal, *data):
        """Exported method used by the core to emit a signal to the client"""
        try:
            if data != None:
                for callback in self.signals[signal]:
                    try:
                        gobject.idle_add(callback, *data)
                    except:
                        log.warning("Unable to call callback for signal %s", 
                            signal)
            else:
                for callback in self.signals[signal]:
                    try:
                        gobject.idle_add(callback)
                    except:
                        log.warning("Unable to call callback for signal %s",
                            signal)
        except KeyError:
            log.debug("There are no callbacks registered for signal '%s'", signal)
        
    def connect_to_signal(self, signal, callback):
        """Connect to a signal"""
        try:
            if callback not in self.signals[signal]:
                self.signals[signal].append(callback)
        except KeyError:
            self.signals[signal] = [callback]
        

