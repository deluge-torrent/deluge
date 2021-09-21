# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import subprocess
import sys

from twisted.internet import defer, reactor, ssl
from twisted.internet.protocol import ClientFactory

from deluge import error
from deluge.common import get_localhost_auth, get_version
from deluge.decorators import deprecated
from deluge.transfer import DelugeTransferProtocol

RPC_RESPONSE = 1
RPC_ERROR = 2
RPC_EVENT = 3

log = logging.getLogger(__name__)


def format_kwargs(kwargs):
    return ', '.join([key + '=' + str(value) for key, value in kwargs.items()])


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
        s = self.method + '('
        if self.args:
            s += ', '.join([str(x) for x in self.args])
        if self.kwargs:
            if self.args:
                s += ', '
            s += format_kwargs(self.kwargs)
        s += ')'

        return s

    def format_message(self):
        """
        Returns a properly formatted RPCRequest based on the properties.  Will
        raise a TypeError if the properties haven't been set yet.

        :returns: a properly formatted RPCRequest
        """
        if (
            self.request_id is None
            or self.method is None
            or self.args is None
            or self.kwargs is None
        ):
            raise TypeError(
                'You must set the properties of this object before calling format_message!'
            )

        return (self.request_id, self.method, self.args, self.kwargs)


class DelugeRPCProtocol(DelugeTransferProtocol):
    def connectionMade(self):  # NOQA: N802
        self.__rpc_requests = {}
        # Set the protocol in the daemon so it can send data
        self.factory.daemon.protocol = self
        # Get the address of the daemon that we've connected to
        peer = self.transport.getPeer()
        self.factory.daemon.host = peer.host
        self.factory.daemon.port = peer.port
        self.factory.daemon.connected = True
        log.debug('Connected to daemon at %s:%s..', peer.host, peer.port)
        self.factory.daemon.connect_deferred.callback((peer.host, peer.port))

    def message_received(self, request):
        """
        This method is called whenever we receive a message from the daemon.

        :param request: a tuple that should be either a RPCResponse, RCPError or RPCSignal

        """
        if not isinstance(request, tuple):
            log.debug('Received invalid message: type is not tuple')
            return
        if len(request) < 3:
            log.debug(
                'Received invalid message: number of items in ' 'response is %s',
                len(request),
            )
            return

        message_type = request[0]

        if message_type == RPC_EVENT:
            event = request[1]
            # log.debug('Received RPCEvent: %s', event)
            # A RPCEvent was received from the daemon so run any handlers
            # associated with it.
            if event in self.factory.event_handlers:
                for handler in self.factory.event_handlers[event]:
                    reactor.callLater(0, handler, *request[2])
            return

        request_id = request[1]

        # We get the Deferred object for this request_id to either run the
        # callbacks or the errbacks dependent on the response from the daemon.
        d = self.factory.daemon.pop_deferred(request_id)

        if message_type == RPC_RESPONSE:
            # Run the callbacks registered with this Deferred object
            d.callback(request[2])
        elif message_type == RPC_ERROR:
            # Recreate exception and errback'it
            try:
                # The exception class is located in deluge.error
                try:
                    exception_cls = getattr(error, request[2])
                    exception = exception_cls(*request[3], **request[4])
                except TypeError:
                    log.warning(
                        'Received invalid RPC_ERROR (Old daemon?): %s', request[2]
                    )
                    return

                # Ideally we would chain the deferreds instead of instance
                # checking just to log them. But, that would mean that any
                # errback on the fist deferred should returns it's failure
                # so it could pass back to the 2nd deferred on the chain. But,
                # that does not always happen.
                # So, just do some instance checking and just log rpc error at
                # different levels.
                r = self.__rpc_requests[request_id]
                msg = 'RPCError Message Received!'
                msg += '\n' + '-' * 80
                msg += '\n' + 'RPCRequest: ' + r.__repr__()
                msg += '\n' + '-' * 80
                if isinstance(exception, error.WrappedException):
                    msg += '\n' + exception.type + '\n' + exception.message + ': '
                    msg += exception.traceback
                else:
                    msg += '\n' + request[5] + '\n' + request[2] + ': '
                    msg += str(exception)
                msg += '\n' + '-' * 80

                if not isinstance(exception, error._ClientSideRecreateError):
                    # Let's log these as errors
                    log.error(msg)
                else:
                    # The rest just gets logged in debug level, just to log
                    # what's happening
                    log.debug(msg)
            except Exception:
                import traceback

                log.error(
                    'Failed to handle RPC_ERROR (Old daemon?): %s\nLocal error: %s',
                    request[2],
                    traceback.format_exc(),
                )
            d.errback(exception)
        del self.__rpc_requests[request_id]

    def send_request(self, request):
        """
        Sends a RPCRequest to the server.

        :param request: RPCRequest

        """
        try:
            # Store the DelugeRPCRequest object just in case a RPCError is sent in
            # response to this request.  We use the extra information when printing
            # out the error for debugging purposes.
            self.__rpc_requests[request.request_id] = request
            # log.debug('Sending RPCRequest %s: %s', request.request_id, request)
            # Send the request in a tuple because multiple requests can be sent at once
            self.transfer_message((request.format_message(),))
        except Exception as ex:
            log.warning('Error occurred when sending message: %s', ex)


class DelugeRPCClientFactory(ClientFactory):
    protocol = DelugeRPCProtocol

    def __init__(self, daemon, event_handlers):
        self.daemon = daemon
        self.event_handlers = event_handlers

    def startedConnecting(self, connector):  # NOQA: N802
        log.debug('Connecting to daemon at "%s:%s"...', connector.host, connector.port)

    def clientConnectionFailed(self, connector, reason):  # NOQA: N802
        log.debug(
            'Connection to daemon at "%s:%s" failed: %s',
            connector.host,
            connector.port,
            reason.value,
        )
        self.daemon.connect_deferred.errback(reason)

    def clientConnectionLost(self, connector, reason):  # NOQA: N802
        log.debug(
            'Connection lost to daemon at "%s:%s" reason: %s',
            connector.host,
            connector.port,
            reason.value,
        )
        self.daemon.host = None
        self.daemon.port = None
        self.daemon.username = None
        self.daemon.connected = False

        if (
            self.daemon.disconnect_deferred
            and not self.daemon.disconnect_deferred.called
        ):
            self.daemon.disconnect_deferred.callback(reason.value)
            self.daemon.disconnect_deferred = None

        if self.daemon.disconnect_callback:
            self.daemon.disconnect_callback()


class DaemonProxy(object):
    pass


class DaemonSSLProxy(DaemonProxy):
    def __init__(self, event_handlers=None):
        if event_handlers is None:
            event_handlers = {}
        self.__factory = DelugeRPCClientFactory(self, event_handlers)
        self.__factory.noisy = False
        self.__request_counter = 0
        self.__deferred = {}

        # This is set when a connection is made to the daemon
        self.protocol = None

        # This is set when a connection is made
        self.host = None
        self.port = None
        self.username = None
        self.authentication_level = 0

        self.connected = False

        self.disconnect_deferred = None
        self.disconnect_callback = None

        self.auth_levels_mapping = None
        self.auth_levels_mapping_reverse = None

    def connect(self, host, port):
        """
        Connects to a daemon at host:port

        :param host: str, the host to connect to
        :param port: int, the listening port on the daemon

        :returns: twisted.Deferred

        """
        log.debug('sslproxy.connect()')
        self.host = host
        self.port = port
        self.__connector = reactor.connectSSL(
            self.host, self.port, self.__factory, ssl.ClientContextFactory()
        )
        self.connect_deferred = defer.Deferred()
        self.daemon_info_deferred = defer.Deferred()

        # Upon connect we do a 'daemon.login' RPC
        self.connect_deferred.addCallback(self.__on_connect)
        self.connect_deferred.addErrback(self.__on_connect_fail)

        return self.daemon_info_deferred

    def disconnect(self):
        log.debug('sslproxy.disconnect()')
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
                self.call('daemon.set_event_interest', [event])

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
        if (
            event in self.__factory.event_handlers
            and handler in self.__factory.event_handlers[event]
        ):
            self.__factory.event_handlers[event].remove(handler)

    def __on_connect(self, result):
        log.debug('__on_connect called')

        def on_info(daemon_info):
            self.daemon_info = daemon_info
            log.debug('Got info from daemon: %s', daemon_info)
            self.daemon_info_deferred.callback(daemon_info)

        def on_info_fail(reason):
            log.debug('Failed to get info from daemon')
            log.exception(reason)
            self.daemon_info_deferred.errback(reason)

        self.call('daemon.info').addCallback(on_info).addErrback(on_info_fail)
        return self.daemon_info_deferred

    def __on_connect_fail(self, reason):
        self.daemon_info_deferred.errback(reason)

    def authenticate(self, username, password):
        log.debug('%s.authenticate: %s', self.__class__.__name__, username)
        login_deferred = defer.Deferred()
        d = self.call('daemon.login', username, password, client_version=get_version())
        d.addCallbacks(
            self.__on_login,
            self.__on_login_fail,
            callbackArgs=[username, login_deferred],
            errbackArgs=[login_deferred],
        )
        return login_deferred

    def __on_login(self, result, username, login_deferred):
        log.debug('__on_login called: %s %s', username, result)
        self.username = username
        self.authentication_level = result
        # We need to tell the daemon what events we're interested in receiving
        if self.__factory.event_handlers:
            self.call('daemon.set_event_interest', list(self.__factory.event_handlers))
            self.call('core.get_auth_levels_mappings').addCallback(
                self.__on_auth_levels_mappings
            )

        login_deferred.callback(result)

    def __on_login_fail(self, result, login_deferred):
        login_deferred.errback(result)

    def __on_auth_levels_mappings(self, result):
        auth_levels_mapping, auth_levels_mapping_reverse = result
        self.auth_levels_mapping = auth_levels_mapping
        self.auth_levels_mapping_reverse = auth_levels_mapping_reverse

    def set_disconnect_callback(self, cb):
        """
        Set a function to be called when the connection to the daemon is lost
        for any reason.
        """
        self.disconnect_callback = cb

    def get_bytes_recv(self):
        return self.protocol.get_bytes_recv()

    def get_bytes_sent(self):
        return self.protocol.get_bytes_sent()


class DaemonStandaloneProxy(DaemonProxy):
    def __init__(self, event_handlers=None):
        if event_handlers is None:
            event_handlers = {}
        from deluge.core import daemon

        self.__daemon = daemon.Daemon(standalone=True)
        self.__daemon.start()
        log.debug('daemon created!')
        self.connected = True
        self.host = 'localhost'
        self.port = 58846
        # Running in standalone mode, it's safe to import auth level
        from deluge.core.authmanager import (
            AUTH_LEVEL_ADMIN,
            AUTH_LEVELS_MAPPING,
            AUTH_LEVELS_MAPPING_REVERSE,
        )

        self.username = 'localclient'
        self.authentication_level = AUTH_LEVEL_ADMIN
        self.auth_levels_mapping = AUTH_LEVELS_MAPPING
        self.auth_levels_mapping_reverse = AUTH_LEVELS_MAPPING_REVERSE
        # Register the event handlers
        for event in event_handlers:
            for handler in event_handlers[event]:
                self.__daemon.core.eventmanager.register_event_handler(event, handler)

    def disconnect(self):
        self.connected = False
        self.__daemon = None

    def call(self, method, *args, **kwargs):
        # log.debug('call: %s %s %s', method, args, kwargs)

        import copy

        try:
            m = self.__daemon.rpcserver.get_object_method(method)
        except Exception as ex:
            log.exception(ex)
            return defer.fail(ex)
        else:
            return defer.maybeDeferred(m, *copy.deepcopy(args), **copy.deepcopy(kwargs))

    def register_event_handler(self, event, handler):
        """
        Registers a handler function to be called when `:param:event` is
        received from the daemon.

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
        raise Exception('You must make calls in the form of "component.method"')

    def __getattr__(self, name):
        return RemoteMethod(self.daemon, self.base + '.' + name)


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

    __event_handlers = {}

    def __init__(self):
        self._daemon_proxy = None
        self.disconnect_callback = None
        self.__started_standalone = False

    def connect(
        self,
        host='127.0.0.1',
        port=58846,
        username='',
        password='',
        skip_authentication=False,
    ):
        """
        Connects to a daemon process.

        :param host: str, the hostname of the daemon
        :param port: int, the port of the daemon
        :param username: str, the username to login with
        :param password: str, the password to login with

        :returns: a Deferred object that will be called once the connection
            has been established or fails
        """

        self._daemon_proxy = DaemonSSLProxy(dict(self.__event_handlers))
        self._daemon_proxy.set_disconnect_callback(self.__on_disconnect)

        d = self._daemon_proxy.connect(host, port)

        def on_connected(daemon_version):
            log.debug('on_connected. Daemon version: %s', daemon_version)
            return daemon_version

        def on_connect_fail(reason):
            log.debug('on_connect_fail: %s', reason)
            self.disconnect()
            return reason

        def on_authenticate(result, daemon_info):
            log.debug('Authentication successful: %s', result)
            return result

        def on_authenticate_fail(reason):
            log.debug('Failed to authenticate: %s', reason.value)
            return reason

        def authenticate(daemon_version, username, password):
            if not username and host in ('127.0.0.1', 'localhost'):
                # No username provided and it's localhost, so attempt to get credentials from auth file.
                username, password = get_localhost_auth()

            d = self._daemon_proxy.authenticate(username, password)
            d.addCallback(on_authenticate, daemon_version)
            d.addErrback(on_authenticate_fail)
            return d

        d.addCallback(on_connected)
        d.addErrback(on_connect_fail)
        if not skip_authentication:
            d.addCallback(authenticate, username, password)
        return d

    def disconnect(self):
        """
        Disconnects from the daemon.
        """
        if self.is_standalone():
            self._daemon_proxy.disconnect()
            self.stop_standalone()
            return defer.succeed(True)

        if self._daemon_proxy:
            return self._daemon_proxy.disconnect()

    def start_standalone(self):
        """
        Starts a daemon in the same process as the client.
        """
        self._daemon_proxy = DaemonStandaloneProxy(self.__event_handlers)
        self.__started_standalone = True

    def stop_standalone(self):
        """
        Stops the daemon process in the client.
        """
        self._daemon_proxy = None
        self.__started_standalone = False

    @deprecated
    def start_classic_mode(self):
        """Deprecated: Use start_standalone"""
        self.start_standalone()

    @deprecated
    def stop_classic_mode(self):
        """Deprecated: Use stop_standalone"""
        self.stop_standalone()

    def start_daemon(self, port, config):
        """Starts a daemon process.

        Args:
            port (int): Port for the daemon to listen on.
            config (str): Config path to pass to daemon.

        Returns:
            bool: True is successfully started the daemon, False otherwise.

        """
        # subprocess.popen does not work with unicode args (with non-ascii characters) on windows
        config = config.encode(sys.getfilesystemencoding())
        try:
            subprocess.Popen(['deluged', '--port=%s' % port, b'--config=%s' % config])
        except OSError as ex:
            from errno import ENOENT

            if ex.errno == ENOENT:
                log.error(
                    _(
                        'Deluge cannot find the `deluged` executable, check that '
                        'the deluged package is installed, or added to your PATH.'
                    )
                )
            else:
                log.exception(ex)
        except Exception as ex:
            log.error('Unable to start daemon!')
            log.exception(ex)
        else:
            return True
        return False

    def is_localhost(self):
        """
        Checks if the current connected host is a localhost or not.

        :returns: bool, True if connected to a localhost

        """
        if (
            self._daemon_proxy
            and self._daemon_proxy.host in ('127.0.0.1', 'localhost')
            or isinstance(self._daemon_proxy, DaemonStandaloneProxy)
        ):
            return True
        return False

    def is_standalone(self):
        """
        Checks to see if the client has been started in standalone mode.

        :returns: bool, True if in standalone mode

        """
        return self.__started_standalone

    @deprecated
    def is_classicmode(self):
        """Deprecated: Use is_standalone"""
        self.is_standalone()

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
            return (
                self._daemon_proxy.host,
                self._daemon_proxy.port,
                self._daemon_proxy.username,
            )

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

    def get_auth_user(self):
        """
        Returns the current authenticated username.

        :returns: the authenticated username
        :rtype: str
        """
        return self._daemon_proxy.username

    def get_auth_level(self):
        """
        Returns the authentication level the daemon returned upon authentication.

        :returns: the authentication level
        :rtype: int
        """
        return self._daemon_proxy.authentication_level

    @property
    def auth_levels_mapping(self):
        return self._daemon_proxy.auth_levels_mapping

    @property
    def auth_levels_mapping_reverse(self):
        return self._daemon_proxy.auth_levels_mapping_reverse


# This is the object clients will use
client = Client()
