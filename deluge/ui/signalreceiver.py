#
# signalreceiver.py
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

import sys
import deluge.SimpleXMLRPCServer as SimpleXMLRPCServer
from SocketServer import ThreadingMixIn
import xmlrpclib as xmlrpclib
import threading

from deluge.log import LOG as log

class SignalReceiver(
        threading.Thread, 
        ThreadingMixIn, 
        SimpleXMLRPCServer.SimpleXMLRPCServer):
    
    def __init__(self, port, core_uri):
        log.debug("SignalReceiver init..")
        threading.Thread.__init__(self)

        # Daemonize the thread so it exits when the main program does
        self.setDaemon(True)
        
        # Setup the xmlrpc server
        try:
            SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(
                self, ("localhost", port), logRequests=False, allow_none=True)
        except:
            log.info("SignalReceiver already running or port not available..")
            sys.exit(0)
        
        self.signals = {}
        
        # Register the emit_signal function
        self.register_function(self.emit_signal)
        
        # Register the signal receiver with the core
        # FIXME: send actual URI not localhost
        core = xmlrpclib.ServerProxy(core_uri)
        core.register_client("http://localhost:" + str(port))
    
    def run(self):
        """This gets called when we start the thread"""
        t = threading.Thread(target=self.serve_forever)
        t.start()
        
    def emit_signal(self, signal, data):
        """Exported method used by the core to emit a signal to the client"""
        log.debug("Received signal %s with data %s from core..", signal, data)
        try:
            if data != None:
                for callback in self.signals[signal]:
                    try:
                        callback(data)
                    except:
                        log.warning("Unable to call callback for signal %s", 
                            signal)
            else:
                for callback in self.signals[signal]:
                    try:
                        callback()
                    except:
                        log.warning("Unable to call callback for signal %s",
                            signal)
        except KeyError:
            log.debug("There are no callbacks registered for this signal..")
        
    def connect_to_signal(self, signal, callback):
        """Connect to a signal"""
        try:
            self.signals[signal].append(callback)
        except KeyError:
            self.signals[signal] = [callback]
        

