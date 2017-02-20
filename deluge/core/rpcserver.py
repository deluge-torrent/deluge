#
# rpcserver.py
#
# Copyright (C) 2008,2009 Andrew Resch <andrewresch@gmail.com>
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

"""RPCServer Module"""

from __future__ import with_statement

import sys
import zlib
import os
import stat
import traceback

from twisted.internet.protocol import Factory, Protocol
from twisted.internet import ssl, reactor, defer

from OpenSSL import crypto, SSL
from types import FunctionType

try:
    import rencode
except ImportError:
    import deluge.rencode as rencode

from deluge.log import LOG as log

import deluge.component as component
import deluge.configmanager
from deluge.core.authmanager import AUTH_LEVEL_NONE, AUTH_LEVEL_DEFAULT

RPC_RESPONSE = 1
RPC_ERROR = 2
RPC_EVENT = 3

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
        doc = func.__doc__
        func.__doc__ = "**RPC Exported Function** (*Auth Level: %s*)\n\n" % auth_level
        if doc:
            func.__doc__ += doc

        return func

    if type(auth_level) is FunctionType:
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
        s = call[1] + "("
        if call[2]:
            s += ", ".join([str(x) for x in call[2]])
        if call[3]:
            if call[2]:
                s += ", "
            s += ", ".join([key + "=" + str(value) for key, value in call[3].items()])
        s += ")"
    except UnicodeEncodeError:
        return "UnicodeEncodeError, call: %s" % call
    else:
        return s

class DelugeError(Exception):
    pass

class NotAuthorizedError(DelugeError):
    pass

class ServerContextFactory(object):
    def getContext(self):
        """
        Create an SSL context.

        This loads the servers cert/private key SSL files for use with the
        SSL transport.
        """
        ssl_dir = deluge.configmanager.get_config_dir("ssl")
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.set_options(SSL.OP_NO_SSLv2 | SSL.OP_NO_SSLv3)
        ctx.use_certificate_file(os.path.join(ssl_dir, "daemon.cert"))
        ctx.use_privatekey_file(os.path.join(ssl_dir, "daemon.pkey"))
        return ctx

class DelugeRPCProtocol(Protocol):
    __buffer = None

    def dataReceived(self, data):
        """
        This method is called whenever data is received from a client.  The
        only message that a client sends to the server is a RPC Request message.
        If the RPC Request message is valid, then the method is called in
        :meth:`dispatch`.

        :param data: the data from the client. It should be a zlib compressed
            rencoded string.
        :type data: str

        """
        if self.__buffer:
            # We have some data from the last dataReceived() so lets prepend it
            data = self.__buffer + data
            self.__buffer = None

        while data:
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

            if len(request) < 1:
                log.debug("Received invalid message: there are no items")
                return

            for call in request:
                if len(call) != 4:
                    log.debug("Received invalid rpc request: number of items in request is %s", len(call))
                    continue
                #log.debug("RPCRequest: %s", format_request(call))
                reactor.callLater(0, self.dispatch, *call)

    def sendData(self, data):
        """
        Sends the data to the client.

        :param data: the object that is to be sent to the client.  This should
            be one of the RPC message types.
        :type data: object

        """
        self.transport.write(zlib.compress(rencode.dumps(data)))

    def connectionMade(self):
        """
        This method is called when a new client connects.
        """
        peer = self.transport.getPeer()
        log.info("Deluge Client connection made from: %s:%s", peer.host, peer.port)
        # Set the initial auth level of this session to AUTH_LEVEL_NONE and empty username.
        self.factory.authorized_sessions[self.transport.sessionno] = (AUTH_LEVEL_NONE, "")

    def connectionLost(self, reason):
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

        log.info("Deluge client disconnected: %s", reason.value)

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
        def sendError():
            """
            Sends an error response with the contents of the exception that was raised.
            """
            exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()

            self.sendData((
                RPC_ERROR,
                request_id,
                (exceptionType.__name__,
                exceptionValue.args[0] if len(exceptionValue.args) == 1 else "",
                "".join(traceback.format_tb(exceptionTraceback)))
            ))

        if method == "daemon.login":
            # This is a special case and used in the initial connection process
            # We need to authenticate the user here
            try:
                ret = component.get("AuthManager").authorize(*args, **kwargs)
                if ret:
                    self.factory.authorized_sessions[self.transport.sessionno] = (ret, args[0])
                    self.factory.session_protocols[self.transport.sessionno] = self
            except Exception, e:
                sendError()
                log.exception(e)
            else:
                self.sendData((RPC_RESPONSE, request_id, (ret)))
                if not ret:
                    self.transport.loseConnection()
            finally:
                return
        elif method == "daemon.set_event_interest" and self.transport.sessionno in self.factory.authorized_sessions:
            # This special case is to allow clients to set which events they are
            # interested in receiving.
            # We are expecting a sequence from the client.
            try:
                if self.transport.sessionno not in self.factory.interested_events:
                    self.factory.interested_events[self.transport.sessionno] = []
                self.factory.interested_events[self.transport.sessionno].extend(args[0])
            except Exception, e:
                sendError()
            else:
                self.sendData((RPC_RESPONSE, request_id, (True)))
            finally:
                return

        if method in self.factory.methods and self.transport.sessionno in self.factory.authorized_sessions:
            try:
                method_auth_requirement = self.factory.methods[method]._rpcserver_auth_level
                auth_level = self.factory.authorized_sessions[self.transport.sessionno][0]
                if auth_level < method_auth_requirement:
                    # This session is not allowed to call this method
                    log.debug("Session %s is trying to call a method it is not authorized to call!", self.transport.sessionno)
                    raise NotAuthorizedError("Auth level too low: %s < %s" % (auth_level, method_auth_requirement))
                # Set the session_id in the factory so that methods can know
                # which session is calling it.
                self.factory.session_id = self.transport.sessionno
                ret = self.factory.methods[method](*args, **kwargs)
            except Exception, e:
                sendError()
                # Don't bother printing out DelugeErrors, because they are just for the client
                if not isinstance(e, DelugeError):
                    log.exception("Exception calling RPC request: %s", e)
            else:
                # Check if the return value is a deferred, since we'll need to
                # wait for it to fire before sending the RPC_RESPONSE
                if isinstance(ret, defer.Deferred):
                    def on_success(result):
                        self.sendData((RPC_RESPONSE, request_id, result))
                        return result

                    def on_fail(failure):
                        try:
                            failure.raiseException()
                        except Exception, e:
                            sendError()
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

    def __init__(self, port=58846, interface="", allow_remote=False, listen=True):
        component.Component.__init__(self, "RPCServer")

        self.factory = Factory()
        self.factory.protocol = DelugeRPCProtocol
        self.factory.session_id = -1

        # Holds the registered methods
        self.factory.methods = {}
        # Holds the session_ids and auth levels
        self.factory.authorized_sessions = {}
        # Holds the protocol objects with the session_id as key
        self.factory.session_protocols = {}
        # Holds the interested event list for the sessions
        self.factory.interested_events = {}

        if not listen:
            return

        if allow_remote:
            hostname = ""
        else:
            hostname = "localhost"

        if interface:
            hostname = interface

        log.info("Starting DelugeRPC server %s:%s", hostname, port)

        # Check for SSL keys and generate some if needed
        check_ssl_keys()

        try:
            reactor.listenSSL(port, self.factory, ServerContextFactory(), interface=hostname)
        except Exception, e:
            log.info("Daemon already running or port not available..")
            log.error(e)
            sys.exit(0)

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
            if d[0] == "_":
                continue
            if getattr(getattr(obj, d), '_rpcserver_export', False):
                log.debug("Registering method: %s", name + "." + d)
                self.factory.methods[name + "." + d] = getattr(obj, d)

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
        return self.factory.methods.keys()

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
        session_id = self.get_session_id()
        if session_id > -1 and session_id in self.factory.authorized_sessions:
            return self.factory.authorized_sessions[session_id][1]
        else:
            # No connections made yet
            return ""

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
        log.debug("intevents: %s", self.factory.interested_events)
        # Find sessions interested in this event
        for session_id, interest in self.factory.interested_events.items():
            if event.name in interest:
                log.debug("Emit Event: %s %s", event.name, event.args)
                # This session is interested so send a RPC_EVENT
                self.factory.session_protocols[session_id].sendData(
                    (RPC_EVENT, event.name, event.args)
                )

def check_ssl_keys():
    """
    Check for SSL cert/key and create them if necessary
    """
    ssl_dir = deluge.configmanager.get_config_dir("ssl")
    if not os.path.exists(ssl_dir):
        # The ssl folder doesn't exist so we need to create it
        os.makedirs(ssl_dir)
        generate_ssl_keys()
    else:
        for f in ("daemon.pkey", "daemon.cert"):
            if not os.path.exists(os.path.join(ssl_dir, f)):
                generate_ssl_keys()
                break

def generate_ssl_keys():
    """
    This method generates a new SSL key/cert.
    """
    digest = "sha256"
    # Generate key pair
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)

    # Generate cert request
    req = crypto.X509Req()
    subj = req.get_subject()
    setattr(subj, "CN", "Deluge Daemon")
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
    ssl_dir = deluge.configmanager.get_config_dir("ssl")
    with open(os.path.join(ssl_dir, "daemon.pkey"), "w") as _file:
        _file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
    with open(os.path.join(ssl_dir, "daemon.cert"), "w") as _file:
        _file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    # Make the files only readable by this user
    for f in ("daemon.pkey", "daemon.cert"):
        os.chmod(os.path.join(ssl_dir, f), stat.S_IREAD | stat.S_IWRITE)
