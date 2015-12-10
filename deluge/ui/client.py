#
# client.py
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
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA  02110-1301, USA.
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

from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor, ssl, defer
try:
    import rencode
except ImportError:
    import deluge.rencode as rencode

import zlib
import subprocess

import deluge.common
import deluge.component as component
from deluge.log import LOG as log

RPC_RESPONSE = 1
RPC_ERROR = 2
RPC_EVENT = 3

def format_kwargs(kwargs):
    return ", ".join([key + "=" + str(value) for key, value in kwargs.items()])

class DelugeRPCError(object):
    """
    This object is passed to errback handlers in the event of a RPCError from the
    daemon.
    """
    def __init__(self, method, args, kwargs, exception_type, exception_msg, traceback):
        self.method = method
        self.args = args
        self.kwargs = kwargs
        self.exception_type = exception_type
        self.exception_msg = exception_msg
        self.traceback = traceback

class DelugeRPCRequest(object):
    """
    This object is created whenever there is a RPCRequest to be sent to the
    daemon.  It is generally only used by the DaemonProxy's call method.
    """

    request_id = None
    method = None
    args = None
    kwargs = None

    def __repr__(self):
        """
        Returns a string of the RPCRequest in the following form:
            method(arg, kwarg=foo, ...)
        """
        s = self.method + "("
        if self.args:
            s += ", ".join([str(x) for x in self.args])
        if self.kwargs:
            if self.args:
                s += ", "
            s += format_kwargs(self.kwargs)
        s += ")"

        return s

    def format_message(self):
        """
        Returns a properly formatted RPCRequest based on the properties.  Will
        raise a TypeError if the properties haven't been set yet.

        :returns: a properly formated RPCRequest
        """
        if self.request_id is None or self.method is None or self.args is None or self.kwargs is None:
            raise TypeError("You must set the properties of this object before calling format_message!")

        return (self.request_id, self.method, self.args, self.kwargs)

class DelugeRPCProtocol(Protocol):
    def connectionMade(self):
        self.__rpc_requests = {}
        self.__buffer = None
        # Set the protocol in the daemon so it can send data
        self.factory.daemon.protocol = self
        # Get the address of the daemon that we've connected to
        peer = self.transport.getPeer()
        self.factory.daemon.host = peer.host
        self.factory.daemon.port = peer.port
        self.factory.daemon.connected = True

        log.info("Connected to daemon at %s:%s..", peer.host, peer.port)
        self.factory.daemon.connect_deferred.callback((peer.host, peer.port))

    def dataReceived(self, data):
        """
        This method is called whenever we receive data from the daemon.

        :param data: a zlib compressed and rencoded string that should be either
            a RPCResponse, RCPError or RPCSignal
        """
        if self.__buffer:
            # We have some data from the last dataReceived() so lets prepend it
            data = self.__buffer + data
            self.__buffer = None

        while data:
            # Increase the byte counter
            self.factory.bytes_recv += len(data)

            dobj = zlib.decompressobj()
            try:
                request = rencode.loads(dobj.decompress(data))
            except Exception, e:
                #log.debug("Received possible invalid message (%r): %s", data, e)
                # This could be cut-off data, so we'll save this in the buffer
                # and try to prepend it on the next dataReceived()
                self.__buffer = data
                return
            else:
                data = dobj.unused_data

            if type(request) is not tuple:
                log.debug("Received invalid message: type is not tuple")
                return
            if len(request) < 3:
                log.debug("Received invalid message: number of items in response is %s", len(3))
                return

            message_type = request[0]

            if message_type == RPC_EVENT:
                event = request[1]
                #log.debug("Received RPCEvent: %s", event)
                # A RPCEvent was received from the daemon so run any handlers
                # associated with it.
                if event in self.factory.event_handlers:
                    for handler in self.factory.event_handlers[event]:
                        reactor.callLater(0, handler, *request[2])
                continue

            request_id = request[1]

            # We get the Deferred object for this request_id to either run the
            # callbacks or the errbacks dependent on the response from the daemon.
            d = self.factory.daemon.pop_deferred(request_id)

            if message_type == RPC_RESPONSE:
                # Run the callbacks registered with this Deferred object
                d.callback(request[2])
            elif message_type == RPC_ERROR:
                # Create the DelugeRPCError to pass to the errback
                r = self.__rpc_requests[request_id]
                e = DelugeRPCError(r.method, r.args, r.kwargs, request[2][0], request[2][1], request[2][2])
                # Run the errbacks registered with this Deferred object
                d.errback(e)

            del self.__rpc_requests[request_id]

    def send_request(self, request):
        """
        Sends a RPCRequest to the server.

        :param request: RPCRequest

        """
        # Store the DelugeRPCRequest object just in case a RPCError is sent in
        # response to this request.  We use the extra information when printing
        # out the error for debugging purposes.
        self.__rpc_requests[request.request_id] = request
        #log.debug("Sending RPCRequest %s: %s", request.request_id, request)
        # Send the request in a tuple because multiple requests can be sent at once
        data = zlib.compress(rencode.dumps((request.format_message(),)))
        self.factory.bytes_sent += len(data)
        self.transport.write(data)

class DelugeRPCClientFactory(ClientFactory):
    protocol = DelugeRPCProtocol

    def __init__(self, daemon, event_handlers):
        self.daemon = daemon
        self.event_handlers = event_handlers

        self.bytes_recv = 0
        self.bytes_sent = 0

    def startedConnecting(self, connector):
        log.info("Connecting to daemon at %s:%s..", connector.host, connector.port)

    def clientConnectionFailed(self, connector, reason):
        log.warning("Connection to daemon at %s:%s failed: %s", connector.host, connector.port, reason.value)
        self.daemon.connect_deferred.errback(reason)

    def clientConnectionLost(self, connector, reason):
        log.info("Connection lost to daemon at %s:%s reason: %s", connector.host, connector.port, reason.value)
        self.daemon.host = None
        self.daemon.port = None
        self.daemon.username = None
        self.daemon.connected = False
        if self.daemon.disconnect_deferred:
            self.daemon.disconnect_deferred.callback(reason.value)

        if self.daemon.disconnect_callback:
            self.daemon.disconnect_callback()

class DaemonProxy(object):
    pass

class DaemonSSLProxy(DaemonProxy):
    def __init__(self, event_handlers=None):
        if event_handlers is None:
            event_handlers = {}
        self.__factory = DelugeRPCClientFactory(self, event_handlers)
        self.__request_counter = 0
        self.__deferred = {}

        # This is set when a connection is made to the daemon
        self.protocol = None

        # This is set when a connection is made
        self.host = None
        self.port = None
        self.username = None

        self.connected = False

        self.disconnect_deferred = None
        self.disconnect_callback = None

    def connect(self, host, port, username, password):
        """
        Connects to a daemon at host:port

        :param host: str, the host to connect to
        :param port: int, the listening port on the daemon
        :param username: str, the username to login as
        :param password: str, the password to login with

        :returns: twisted.Deferred

        """
        self.host = host
        self.port = port
        self.__connector = reactor.connectSSL(self.host, self.port, self.__factory, ssl.ClientContextFactory())
        self.connect_deferred = defer.Deferred()
        self.login_deferred = defer.Deferred()

        # Upon connect we do a 'daemon.login' RPC
        self.connect_deferred.addCallback(self.__on_connect, username, password)
        self.connect_deferred.addErrback(self.__on_connect_fail)

        return self.login_deferred

    def disconnect(self):
        self.disconnect_deferred = defer.Deferred()
        self.__connector.disconnect()
        return self.disconnect_deferred

    def call(self, method, *args, **kwargs):
        """
        Makes a RPCRequest to the daemon.  All methods should be in the form of
        'component.method'.

        :params method: str, the method to call in the form of 'component.method'
        :params args: the arguments to call the remote method with
        :params kwargs: the keyword arguments to call the remote method with

        :return: a twisted.Deferred object that will be activated when a RPCResponse
            or RPCError is received from the daemon

        """
        # Create the DelugeRPCRequest to pass to protocol.send_request()
        request = DelugeRPCRequest()
        request.request_id = self.__request_counter
        request.method = method
        request.args = args
        request.kwargs = kwargs
        # Send the request to the server
        self.protocol.send_request(request)
        # Create a Deferred object to return and add a default errback to print
        # the error.
        d = defer.Deferred()
        d.addErrback(self.__rpcError)

        # Store the Deferred until we receive a response from the daemon
        self.__deferred[self.__request_counter] = d

        # Increment the request counter since we don't want to use the same one
        # before a response is received.
        self.__request_counter += 1

        return d

    def pop_deferred(self, request_id):
        """
        Pops a Deferred object.  This is generally called once we receive the
        reply we were waiting on from the server.

        :param request_id: the request_id of the Deferred to pop
        :type request_id: int

        """
        return self.__deferred.pop(request_id)

    def register_event_handler(self, event, handler):
        """
        Registers a handler function to be called when `:param:event` is received
        from the daemon.

        :param event: the name of the event to handle
        :type event: str
        :param handler: the function to be called when `:param:event`
            is emitted from the daemon
        :type handler: function

        """
        if event not in self.__factory.event_handlers:
            # This is a new event to handle, so we need to tell the daemon
            # that we're interested in receiving this type of event
            self.__factory.event_handlers[event] = []
            if self.connected:
                self.call("daemon.set_event_interest", [event])

        # Only add the handler if it's not already registered
        if handler not in self.__factory.event_handlers[event]:
            self.__factory.event_handlers[event].append(handler)

    def deregister_event_handler(self, event, handler):
        """
        Deregisters a event handler.

        :param event: the name of the event
        :type event: str
        :param handler: the function registered
        :type handler: function

        """
        if event in self.__factory.event_handlers and handler in self.__factory.event_handlers[event]:
            self.__factory.event_handlers[event].remove(handler)

    def __rpcError(self, error_data):
        """
        Prints out a RPCError message to the error log.  This includes the daemon
        traceback.

        :param error_data: this is passed from the deferred errback with error.value
            containing a `:class:DelugeRPCError` object.
        """
        # Get the DelugeRPCError object from the error_data
        error = error_data.value
        # Create a delugerpcrequest to print out a nice RPCRequest string
        r = DelugeRPCRequest()
        r.method = error.method
        r.args = error.args
        r.kwargs = error.kwargs
        msg = "RPCError Message Received!"
        msg += "\n" + "-" * 80
        msg += "\n" + "RPCRequest: " + r.__repr__()
        msg += "\n" + "-" * 80
        msg += "\n" + error.traceback + "\n" + error.exception_type + ": " + error.exception_msg
        msg += "\n" + "-" * 80
        log.error(msg)
        return error_data

    def __on_connect(self, result, username, password):
        self.__login_deferred = self.call("daemon.login", username, password)
        self.__login_deferred.addCallback(self.__on_login, username)
        self.__login_deferred.addErrback(self.__on_login_fail)

    def __on_connect_fail(self, reason):
        log.debug("connect_fail: %s", reason)
        self.login_deferred.errback(reason)

    def __on_login(self, result, username):
        self.username = username
        # We need to tell the daemon what events we're interested in receiving
        if self.__factory.event_handlers:
            self.call("daemon.set_event_interest", self.__factory.event_handlers.keys())
        self.login_deferred.callback(result)

    def __on_login_fail(self, result):
        log.debug("_on_login_fail(): %s", result)
        self.login_deferred.errback(result)

    def set_disconnect_callback(self, cb):
        """
        Set a function to be called when the connection to the daemon is lost
        for any reason.
        """
        self.disconnect_callback = cb

    def get_bytes_recv(self):
        return self.__factory.bytes_recv

    def get_bytes_sent(self):
        return self.__factory.bytes_sent

class DaemonClassicProxy(DaemonProxy):
    def __init__(self, event_handlers=None):
        if event_handlers is None:
            event_handlers = {}
        import deluge.core.daemon
        self.__daemon = deluge.core.daemon.Daemon(classic=True)
        log.debug("daemon created!")
        self.connected = True
        self.host = "localhost"
        self.port = 58846
        self.username = "localclient"
        # Register the event handlers
        for event in event_handlers:
            for handler in event_handlers[event]:
                self.__daemon.core.eventmanager.register_event_handler(event, handler)

    def disconnect(self):
        self.__daemon = None

    def call(self, method, *args, **kwargs):
        #log.debug("call: %s %s %s", method, args, kwargs)

        import copy

        try:
            m = self.__daemon.rpcserver.get_object_method(method)
        except Exception, e:
            log.exception(e)
            return defer.fail(e)
        else:
            return defer.maybeDeferred(m, *copy.deepcopy(args), **copy.deepcopy(kwargs))

    def register_event_handler(self, event, handler):
        """
        Registers a handler function to be called when `:param:event` is received
        from the daemon.

        :param event: the name of the event to handle
        :type event: str
        :param handler: the function to be called when `:param:event`
            is emitted from the daemon
        :type handler: function

        """
        self.__daemon.core.eventmanager.register_event_handler(event, handler)

    def deregister_event_handler(self, event, handler):
        """
        Deregisters a event handler.

        :param event: the name of the event
        :type event: str
        :param handler: the function registered
        :type handler: function

        """
        self.__daemon.core.eventmanager.deregister_event_handler(event, handler)

class DottedObject(object):
    """
    This is used for dotted name calls to client
    """
    def __init__(self, daemon, method):
        self.daemon = daemon
        self.base = method

    def __call__(self, *args, **kwargs):
        raise Exception("You must make calls in the form of 'component.method'!")

    def __getattr__(self, name):
        return RemoteMethod(self.daemon, self.base + "." + name)

class RemoteMethod(DottedObject):
    """
    This is used when something like 'client.core.get_something()' is attempted.
    """
    def __call__(self, *args, **kwargs):
        return self.daemon.call(self.base, *args, **kwargs)

class Client(object):
    """
    This class is used to connect to a daemon process and issue RPC requests.
    """

    __event_handlers = {
    }

    def __init__(self):
        self._daemon_proxy = None
        self.disconnect_callback = None
        self.__started_in_classic = False

    def connect(self, host="127.0.0.1", port=58846, username="", password=""):
        """
        Connects to a daemon process.

        :param host: str, the hostname of the daemon
        :param port: int, the port of the daemon
        :param username: str, the username to login with
        :param password: str, the password to login with

        :returns: a Deferred object that will be called once the connection
            has been established or fails
        """
        if not username and host in ("127.0.0.1", "localhost"):
            # No username was provided and it's the localhost, so we can try
            # to grab the credentials from the auth file.
            import common
            username, password = common.get_localhost_auth()

        self._daemon_proxy = DaemonSSLProxy(dict(self.__event_handlers))
        self._daemon_proxy.set_disconnect_callback(self.__on_disconnect)
        d = self._daemon_proxy.connect(host, port, username, password)
        def on_connect_fail(result):
            log.debug("on_connect_fail: %s", result)
            self.disconnect()
            return result

        d.addErrback(on_connect_fail)
        return d

    def disconnect(self):
        """
        Disconnects from the daemon.
        """
        if self._daemon_proxy:
            return self._daemon_proxy.disconnect()

    def start_classic_mode(self):
        """
        Starts a daemon in the same process as the client.
        """
        self._daemon_proxy = DaemonClassicProxy(self.__event_handlers)
        self.__started_in_classic = True

    def start_daemon(self, port, config):
        """
        Starts a daemon process.

        :param port: the port for the daemon to listen on
        :type port: int
        :param config: the path to the current config folder
        :type config: str
        :returns: True if started, False if not
        :rtype: bool

        :raises OSError: received from subprocess.call()

        """
        try:
            if deluge.common.windows_check():
                subprocess.Popen(["deluged", "--port=%s" % port, "--config=%s" % config])
            else:
                subprocess.call(["deluged", "--port=%s" % port, "--config=%s" % config])
        except OSError, e:
            from errno import ENOENT
            if e.errno == ENOENT:
                log.error(_("Deluge cannot find the 'deluged' executable, it is likely \
that you forgot to install the deluged package or it's not in your PATH."))
            else:
                log.exception(e)
            raise e
        except Exception, e:
            log.error("Unable to start daemon!")
            log.exception(e)
            return False
        else:
            return True

    def is_localhost(self):
        """
        Checks if the current connected host is a localhost or not.

        :returns: bool, True if connected to a localhost

        """
        if self._daemon_proxy and self._daemon_proxy.host in ("127.0.0.1", "localhost") or\
            isinstance(self._daemon_proxy, DaemonClassicProxy):
            return True
        return False

    def is_classicmode(self):
        """
        Checks to see if the client has been started in classic mode.

        :returns: bool, True if in classic mode

        """
        return self.__started_in_classic

    def connected(self):
        """
        Check to see if connected to a daemon.

        :returns: bool, True if connected

        """
        return self._daemon_proxy.connected if self._daemon_proxy else False

    def connection_info(self):
        """
        Get some info about the connection or return None if not connected.

        :returns: a tuple of (host, port, username) or None if not connected
        """
        if self.connected():
            return (self._daemon_proxy.host, self._daemon_proxy.port, self._daemon_proxy.username)

        return None

    def register_event_handler(self, event, handler):
        """
        Registers a handler that will be called when an event is received from the daemon.

        :params event: str, the event to handle
        :params handler: func, the handler function, f(args)
        """
        if event not in self.__event_handlers:
            self.__event_handlers[event] = []
        self.__event_handlers[event].append(handler)
        # We need to replicate this in the daemon proxy
        if self._daemon_proxy:
            self._daemon_proxy.register_event_handler(event, handler)

    def deregister_event_handler(self, event, handler):
        """
        Deregisters a event handler.

        :param event: str, the name of the event
        :param handler: function, the function registered

        """
        if event in self.__event_handlers and handler in self.__event_handlers[event]:
            self.__event_handlers[event].remove(handler)
        if self._daemon_proxy:
            self._daemon_proxy.deregister_event_handler(event, handler)

    def force_call(self, block=False):
        # no-op for now.. we'll see if we need this in the future
        pass

    def __getattr__(self, method):
        return DottedObject(self._daemon_proxy, method)

    def set_disconnect_callback(self, cb):
        """
        Set a function to be called whenever the client is disconnected from
        the daemon for any reason.
        """
        self.disconnect_callback = cb

    def __on_disconnect(self):
        if self.disconnect_callback:
            self.disconnect_callback()

    def get_bytes_recv(self):
        """
        Returns the number of bytes received from the daemon.

        :returns: the number of bytes received
        :rtype: int
        """
        return self._daemon_proxy.get_bytes_recv()

    def get_bytes_sent(self):
        """
        Returns the number of bytes sent to the daemon.

        :returns: the number of bytes sent
        :rtype: int
        """
        return self._daemon_proxy.get_bytes_sent()

# This is the object clients will use
client = Client()
