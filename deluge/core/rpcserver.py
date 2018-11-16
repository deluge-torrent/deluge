# -*- coding: utf-8 -*-
#
# Copyright (C) 2008,2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""RPCServer Module"""
from __future__ import unicode_literals

import logging
import os
import stat
import sys
import traceback
from collections import namedtuple
from types import FunctionType

from OpenSSL import crypto
from twisted.internet import defer, reactor
from twisted.internet.protocol import Factory, connectionDone

import deluge.component as component
import deluge.configmanager
from deluge.core.authmanager import (
    AUTH_LEVEL_ADMIN,
    AUTH_LEVEL_DEFAULT,
    AUTH_LEVEL_NONE,
)
from deluge.crypto_utils import get_context_factory
from deluge.error import (
    DelugeError,
    IncompatibleClient,
    NotAuthorizedError,
    WrappedException,
    _ClientSideRecreateError,
)
from deluge.event import ClientDisconnectedEvent
from deluge.transfer import DelugeTransferProtocol

RPC_RESPONSE = 1
RPC_ERROR = 2
RPC_EVENT = 3

log = logging.getLogger(__name__)


def export(auth_level=AUTH_LEVEL_DEFAULT):
    """
    Decorator function to register an object's method as an RPC.  The object
    will need to be registered with an :class:`RPCServer` to be effective.

    :param func: the function to export
    :type func: function
    :param auth_level: the auth level required to call this method
    :type auth_level: int

    """

    def wrap(func, *args, **kwargs):
        func._rpcserver_export = True
        func._rpcserver_auth_level = auth_level

        rpc_text = '**RPC exported method** (*Auth level: %s*)' % auth_level

        # Append the RPC text while ensuring correct docstring formatting.
        if func.__doc__:
            if func.__doc__.endswith('    '):
                indent = func.__doc__.split('\n')[-1]
                func.__doc__ += '\n{}'.format(indent)
            else:
                func.__doc__ += '\n\n'
            func.__doc__ += rpc_text
        else:
            func.__doc__ = rpc_text

        return func

    if isinstance(auth_level, FunctionType):
        func = auth_level
        auth_level = AUTH_LEVEL_DEFAULT
        return wrap(func)
    else:
        return wrap


def format_request(call):
    """
    Format the RPCRequest message for debug printing

    :param call: the request
    :type call: a RPCRequest

    :returns: a formatted string for printing
    :rtype: str

    """
    try:
        s = call[1] + '('
        if call[2]:
            s += ', '.join([str(x) for x in call[2]])
        if call[3]:
            if call[2]:
                s += ', '
            s += ', '.join([key + '=' + str(value) for key, value in call[3].items()])
        s += ')'
    except UnicodeEncodeError:
        return 'UnicodeEncodeError, call: %s' % call
    else:
        return s


class DelugeRPCProtocol(DelugeTransferProtocol):
    def __init__(self):
        super(DelugeRPCProtocol, self).__init__()
        # namedtuple subclass with auth_level, username for the connected session.
        self.AuthLevel = namedtuple('SessionAuthlevel', 'auth_level, username')

    def message_received(self, request):
        """
        This method is called whenever a message is received from a client.  The
        only message that a client sends to the server is a RPC Request message.
        If the RPC Request message is valid, then the method is called in
        :meth:`dispatch`.

        :param request: the request from the client.
        :type data: tuple

        """
        if not isinstance(request, tuple):
            log.debug('Received invalid message: type is not tuple')
            return

        if len(request) < 1:
            log.debug('Received invalid message: there are no items')
            return

        for call in request:
            if len(call) != 4:
                log.debug(
                    'Received invalid rpc request: number of items ' 'in request is %s',
                    len(call),
                )
                continue
            # log.debug('RPCRequest: %s', format_request(call))
            reactor.callLater(0, self.dispatch, *call)

    def sendData(self, data):  # NOQA: N802
        """
        Sends the data to the client.

        :param data: the object that is to be sent to the client.  This should
            be one of the RPC message types.
        :type data: object

        """
        try:
            self.transfer_message(data)
        except Exception as ex:
            log.warning('Error occurred when sending message: %s.', ex)
            log.exception(ex)
            raise

    def connectionMade(self):  # NOQA: N802
        """
        This method is called when a new client connects.
        """
        peer = self.transport.getPeer()
        log.info('Deluge Client connection made from: %s:%s', peer.host, peer.port)
        # Set the initial auth level of this session to AUTH_LEVEL_NONE
        self.factory.authorized_sessions[self.transport.sessionno] = self.AuthLevel(
            AUTH_LEVEL_NONE, ''
        )

    def connectionLost(self, reason=connectionDone):  # NOQA: N802
        """
        This method is called when the client is disconnected.

        :param reason: the reason the client disconnected.
        :type reason: str

        """

        # We need to remove this session from various dicts
        del self.factory.authorized_sessions[self.transport.sessionno]
        if self.transport.sessionno in self.factory.session_protocols:
            del self.factory.session_protocols[self.transport.sessionno]
        if self.transport.sessionno in self.factory.interested_events:
            del self.factory.interested_events[self.transport.sessionno]

        if self.factory.state == 'running':
            component.get('EventManager').emit(
                ClientDisconnectedEvent(self.factory.session_id)
            )
        log.info('Deluge client disconnected: %s', reason.value)

    def valid_session(self):
        return self.transport.sessionno in self.factory.authorized_sessions

    def dispatch(self, request_id, method, args, kwargs):
        """
        This method is run when a RPC Request is made.  It will run the local method
        and will send either a RPC Response or RPC Error back to the client.

        :param request_id: the request_id from the client (sent in the RPC Request)
        :type request_id: int
        :param method: the local method to call. It must be registered with
            the :class:`RPCServer`.
        :type method: str
        :param args: the arguments to pass to `method`
        :type args: list
        :param kwargs: the keyword-arguments to pass to `method`
        :type kwargs: dict

        """

        def send_error():
            """
            Sends an error response with the contents of the exception that was raised.
            """
            exc_type, exc_value, dummy_exc_trace = sys.exc_info()
            formated_tb = traceback.format_exc()
            try:
                self.sendData(
                    (
                        RPC_ERROR,
                        request_id,
                        exc_type.__name__,
                        exc_value._args,
                        exc_value._kwargs,
                        formated_tb,
                    )
                )
            except AttributeError:
                # This is not a deluge exception (object has no attribute '_args), let's wrap it
                log.warning(
                    'An exception occurred while sending RPC_ERROR to '
                    'client. Wrapping it and resending. Error to '
                    'send(causing exception goes next):\n%s',
                    formated_tb,
                )
                try:
                    raise WrappedException(
                        str(exc_value), exc_type.__name__, formated_tb
                    )
                except WrappedException:
                    send_error()
            except Exception as ex:
                log.error(
                    'An exception occurred while sending RPC_ERROR to client: %s', ex
                )

        if method == 'daemon.info':
            # This is a special case and used in the initial connection process
            self.sendData((RPC_RESPONSE, request_id, deluge.common.get_version()))
            return
        elif method == 'daemon.login':
            # This is a special case and used in the initial connection process
            # We need to authenticate the user here
            log.debug('RPC dispatch daemon.login')
            try:
                client_version = kwargs.pop('client_version', None)
                if client_version is None:
                    raise IncompatibleClient(deluge.common.get_version())
                ret = component.get('AuthManager').authorize(*args, **kwargs)
                if ret:
                    self.factory.authorized_sessions[
                        self.transport.sessionno
                    ] = self.AuthLevel(ret, args[0])
                    self.factory.session_protocols[self.transport.sessionno] = self
            except Exception as ex:
                send_error()
                if not isinstance(ex, _ClientSideRecreateError):
                    log.exception(ex)
            else:
                self.sendData((RPC_RESPONSE, request_id, (ret)))
                if not ret:
                    self.transport.loseConnection()
            return

        # Anything below requires a valid session
        if not self.valid_session():
            return

        if method == 'daemon.set_event_interest':
            log.debug('RPC dispatch daemon.set_event_interest')
            # This special case is to allow clients to set which events they are
            # interested in receiving.
            # We are expecting a sequence from the client.
            try:
                if self.transport.sessionno not in self.factory.interested_events:
                    self.factory.interested_events[self.transport.sessionno] = []
                self.factory.interested_events[self.transport.sessionno].extend(args[0])
            except Exception:
                send_error()
            else:
                self.sendData((RPC_RESPONSE, request_id, (True)))
            return

        if method not in self.factory.methods:
            try:
                # Raise exception to be sent back to client
                raise AttributeError('RPC call on invalid function: %s' % method)
            except AttributeError:
                send_error()
                return

        log.debug('RPC dispatch %s', method)
        try:
            method_auth_requirement = self.factory.methods[method]._rpcserver_auth_level
            auth_level = self.factory.authorized_sessions[
                self.transport.sessionno
            ].auth_level
            if auth_level < method_auth_requirement:
                # This session is not allowed to call this method
                log.debug(
                    'Session %s is attempting an unauthorized method call!',
                    self.transport.sessionno,
                )
                raise NotAuthorizedError(auth_level, method_auth_requirement)
            # Set the session_id in the factory so that methods can know
            # which session is calling it.
            self.factory.session_id = self.transport.sessionno
            ret = self.factory.methods[method](*args, **kwargs)
        except Exception as ex:
            send_error()
            # Don't bother printing out DelugeErrors, because they are just
            # for the client
            if not isinstance(ex, DelugeError):
                log.exception('Exception calling RPC request: %s', ex)
        else:
            # Check if the return value is a deferred, since we'll need to
            # wait for it to fire before sending the RPC_RESPONSE
            if isinstance(ret, defer.Deferred):

                def on_success(result):
                    try:
                        self.sendData((RPC_RESPONSE, request_id, result))
                    except Exception:
                        send_error()
                    return result

                def on_fail(failure):
                    try:
                        failure.raiseException()
                    except Exception:
                        send_error()
                    return failure

                ret.addCallbacks(on_success, on_fail)
            else:
                self.sendData((RPC_RESPONSE, request_id, ret))


class RPCServer(component.Component):
    """
    This class is used to handle rpc requests from the client.  Objects are
    registered with this class and their methods are exported using the export
    decorator.

    :param port: the port the RPCServer will listen on
    :type port: int
    :param interface: the interface to listen on, this may override the `allow_remote` setting
    :type interface: str
    :param allow_remote: set True if the server should allow remote connections
    :type allow_remote: bool
    :param listen: if False, will not start listening.. This is only useful in Classic Mode
    :type listen: bool
    """

    def __init__(self, port=58846, interface='', allow_remote=False, listen=True):
        component.Component.__init__(self, 'RPCServer')

        self.factory = Factory()
        self.factory.protocol = DelugeRPCProtocol
        self.factory.session_id = -1
        self.factory.state = 'running'

        # Holds the registered methods
        self.factory.methods = {}
        # Holds the session_ids and auth levels
        self.factory.authorized_sessions = {}
        # Holds the protocol objects with the session_id as key
        self.factory.session_protocols = {}
        # Holds the interested event list for the sessions
        self.factory.interested_events = {}

        self.listen = listen
        if not listen:
            return

        if allow_remote:
            hostname = ''
        else:
            hostname = 'localhost'

        if interface:
            hostname = interface

        log.info('Starting DelugeRPC server %s:%s', hostname, port)

        # Check for SSL keys and generate some if needed
        check_ssl_keys()

        cert = os.path.join(deluge.configmanager.get_config_dir('ssl'), 'daemon.cert')
        pkey = os.path.join(deluge.configmanager.get_config_dir('ssl'), 'daemon.pkey')

        try:
            reactor.listenSSL(
                port, self.factory, get_context_factory(cert, pkey), interface=hostname
            )
        except Exception as ex:
            log.debug('Daemon already running or port not available.: %s', ex)
            raise

    def register_object(self, obj, name=None):
        """
        Registers an object to export it's rpc methods.  These methods should
        be exported with the export decorator prior to registering the object.

        :param obj: the object that we want to export
        :type obj: object
        :param name: the name to use, if None, it will be the class name of the object
        :type name: str
        """
        if not name:
            name = obj.__class__.__name__.lower()

        for d in dir(obj):
            if d[0] == '_':
                continue
            if getattr(getattr(obj, d), '_rpcserver_export', False):
                log.debug('Registering method: %s', name + '.' + d)
                self.factory.methods[name + '.' + d] = getattr(obj, d)

    def deregister_object(self, obj):
        """
        Deregisters an objects exported rpc methods.

        :param obj: the object that was previously registered

        """
        for key, value in self.factory.methods.items():
            if value.__self__ == obj:
                del self.factory.methods[key]

    def get_object_method(self, name):
        """
        Returns a registered method.

        :param name: the name of the method, usually in the form of 'object.method'
        :type name: str

        :returns: method

        :raises KeyError: if `name` is not registered

        """
        return self.factory.methods[name]

    def get_method_list(self):
        """
        Returns a list of the exported methods.

        :returns: the exported methods
        :rtype: list
        """
        return list(self.factory.methods)

    def get_session_id(self):
        """
        Returns the session id of the current RPC.

        :returns: the session id, this will be -1 if no connections have been made
        :rtype: int

        """
        return self.factory.session_id

    def get_session_user(self):
        """
        Returns the username calling the current RPC.

        :returns: the username of the user calling the current RPC
        :rtype: string

        """
        if not self.listen:
            return 'localclient'
        session_id = self.get_session_id()
        if session_id > -1 and session_id in self.factory.authorized_sessions:
            return self.factory.authorized_sessions[session_id].username
        else:
            # No connections made yet
            return ''

    def get_session_auth_level(self):
        """
        Returns the auth level of the user calling the current RPC.

        :returns: the auth level
        :rtype: int
        """
        if not self.listen or not self.is_session_valid(self.get_session_id()):
            return AUTH_LEVEL_ADMIN
        return self.factory.authorized_sessions[self.get_session_id()].auth_level

    def get_rpc_auth_level(self, rpc):
        """
        Returns the auth level requirement for an exported rpc.

        :returns: the auth level
        :rtype: int
        """
        return self.factory.methods[rpc]._rpcserver_auth_level

    def is_session_valid(self, session_id):
        """
        Checks if the session is still valid, eg, if the client is still connected.

        :param session_id: the session id
        :type session_id: int

        :returns: True if the session is valid
        :rtype: bool

        """
        return session_id in self.factory.authorized_sessions

    def emit_event(self, event):
        """
        Emits the event to interested clients.

        :param event: the event to emit
        :type event: :class:`deluge.event.DelugeEvent`
        """
        log.debug('intevents: %s', self.factory.interested_events)
        # Find sessions interested in this event
        for session_id, interest in self.factory.interested_events.items():
            if event.name in interest:
                log.debug('Emit Event: %s %s', event.name, event.args)
                # This session is interested so send a RPC_EVENT
                self.factory.session_protocols[session_id].sendData(
                    (RPC_EVENT, event.name, event.args)
                )

    def emit_event_for_session_id(self, session_id, event):
        """
        Emits the event to specified session_id.

        :param session_id: the event to emit
        :type session_id: int
        :param event: the event to emit
        :type event: :class:`deluge.event.DelugeEvent`
        """
        if not self.is_session_valid(session_id):
            log.debug(
                'Session ID %s is not valid. Not sending event "%s".',
                session_id,
                event.name,
            )
            return
        if session_id not in self.factory.interested_events:
            log.debug(
                'Session ID %s is not interested in any events. Not sending event "%s".',
                session_id,
                event.name,
            )
            return
        if event.name not in self.factory.interested_events[session_id]:
            log.debug(
                'Session ID %s is not interested in event "%s". Not sending it.',
                session_id,
                event.name,
            )
            return
        log.debug(
            'Sending event "%s" with args "%s" to session id "%s".',
            event.name,
            event.args,
            session_id,
        )
        self.factory.session_protocols[session_id].sendData(
            (RPC_EVENT, event.name, event.args)
        )

    def stop(self):
        self.factory.state = 'stopping'


def check_ssl_keys():
    """
    Check for SSL cert/key and create them if necessary
    """
    ssl_dir = deluge.configmanager.get_config_dir('ssl')
    if not os.path.exists(ssl_dir):
        # The ssl folder doesn't exist so we need to create it
        os.makedirs(ssl_dir)
        generate_ssl_keys()
    else:
        for f in ('daemon.pkey', 'daemon.cert'):
            if not os.path.exists(os.path.join(ssl_dir, f)):
                generate_ssl_keys()
                break


def generate_ssl_keys():
    """
    This method generates a new SSL key/cert.
    """
    from deluge.common import PY2

    digest = 'sha256' if not PY2 else b'sha256'

    # Generate key pair
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)

    # Generate cert request
    req = crypto.X509Req()
    subj = req.get_subject()
    setattr(subj, 'CN', 'Deluge Daemon')
    req.set_pubkey(pkey)
    req.sign(pkey, digest)

    # Generate certificate
    cert = crypto.X509()
    cert.set_serial_number(0)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(60 * 60 * 24 * 365 * 3)  # Three Years
    cert.set_issuer(req.get_subject())
    cert.set_subject(req.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.sign(pkey, digest)

    # Write out files
    ssl_dir = deluge.configmanager.get_config_dir('ssl')
    with open(os.path.join(ssl_dir, 'daemon.pkey'), 'wb') as _file:
        _file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
    with open(os.path.join(ssl_dir, 'daemon.cert'), 'wb') as _file:
        _file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    # Make the files only readable by this user
    for f in ('daemon.pkey', 'daemon.cert'):
        os.chmod(os.path.join(ssl_dir, f), stat.S_IREAD | stat.S_IWRITE)
