#
# rpcserver.py
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
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

"""RPCServer Module"""

import sys
import zlib
import os
import stat
import traceback

from twisted.internet.protocol import Factory, Protocol
from twisted.internet import ssl, reactor

from OpenSSL import crypto, SSL

import deluge.rencode as rencode
from deluge.log import LOG as log

import deluge.component as component
import deluge.configmanager
from deluge.core.authmanager import AUTH_LEVEL_NONE, AUTH_LEVEL_DEFAULT

RPC_RESPONSE = 1
RPC_ERROR = 2
RPC_SIGNAL = 3

def export(auth_level=AUTH_LEVEL_DEFAULT):
    """
    Decorator function to register an object's method as an RPC.  The object
    will need to be registered with an `:class:RPCServer` to be effective.

    :param func: function, the function to export
    :param auth_level: int, the auth level required to call this method

    """
    def wrap(func, *args, **kwargs):
        func._rpcserver_export = True
        func._rpcserver_auth_level = auth_level
        return func

    return wrap

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
        ctx.use_certificate_file(os.path.join(ssl_dir, "daemon.cert"))
        ctx.use_privatekey_file(os.path.join(ssl_dir, "daemon.pkey"))
        return ctx

class DelugeRPCProtocol(Protocol):
    __buffer = None

    def dataReceived(self, data):
        """
        This method is called whenever data is received from a client.  The
        only message that a client sends to the server is a RPC Request message.
        If the RPC Request message is valid, then the method is called in a thread
        with _dispatch().

        :param data: str, the data from the client. It should be a zlib compressed
            rencoded string.

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
                log.debug("Received possible invalid message (%r): %s", data, e)
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

                # Format the RPCRequest message for debug printing
                s = call[1] + "("
                if call[2]:
                    s += ", ".join([str(x) for x in call[2]])
                if call[3]:
                    if call[2]:
                        s += ", "
                    s += ", ".join([key + "=" + str(value) for key, value in call[3].items()])
                s += ")"

                log.debug("RPCRequest: %s", s)
                reactor.callLater(0, self._dispatch, *call)

    def sendData(self, data):
        """
        Sends the data to the client.

        :param data: the object that is to be sent to the client.  This should
            be one of the RPC message types.

        """
        self.transport.write(zlib.compress(rencode.dumps(data)))

    def connectionMade(self):
        """
        This method is called when a new client connects.
        """
        peer = self.transport.getPeer()
        log.info("Deluge Client connection made from: %s:%s", peer.host, peer.port)
        # Set the initial auth level of this session to AUTH_LEVEL_NONE
        self.factory.authorized_sessions[self.transport.sessionno] = AUTH_LEVEL_NONE

    def connectionLost(self, reason):
        """
        This method is called when the client is disconnected.

        :param reason: str, the reason the client disconnected.

        """

        # We need to remove this session from the authmanager
        del self.factory.authorized_sessions[self.transport.sessionno]

        log.info("Deluge client disconnected: %s", reason.value)

    def _dispatch(self, request_id, method, args, kwargs):
        """
        This method is run when a RPC Request is made.  It will run the local method
        and will send either a RPC Response or RPC Error back to the client.

        :param request_id: int, the request_id from the client (sent in the RPC Request)
        :param method: str, the local method to call. It must be registered with
            the `:class:RPCServer`.
        :param args: list, the arguments to pass to `:param:method`
        :param kwargs: dict, the keyword-arguments to pass to `:param:method`

        """
        if method == "daemon.login":
            # This is a special case and used in the initial connection process
            # We need to authenticate the user here
            try:
                ret = component.get("AuthManager").authorize(*args, **kwargs)
                if ret:
                    self.factory.authorized_sessions[self.transport.sessionno] = ret
            except Exception, e:
                # Send error packet here
                log.exception(e)
            else:
                self.sendData((RPC_RESPONSE, request_id, (ret)))
                if not ret:
                    self.transport.loseConnection()
            finally:
                return
        elif method == "daemon.list_methods":
            # This is a method used to populate the json-rpc interface in the
            # webui
            try:
                ret = self.factory.methods.keys()
            except Exception, e:
                # Send error packet here
                log.exception(e)
            else:
                self.sendData((RPC_RESPONSE, request_id, (ret)))
                if not ret:
                    self.transport.loseConnection()
            finally:
                return

        if method in self.factory.methods:
            try:
                method_auth_requirement = self.factory.methods[method]._rpcserver_auth_level
                auth_level = self.factory.authorized_sessions[self.transport.sessionno]
                if auth_level < method_auth_requirement:
                    # This session is not allowed to call this method
                    log.debug("Session %s is trying to call a method it is not authorized to call!", self.transport.sessionno)
                    raise NotAuthorizedError("Auth level too low: %s < %s" % (auth_level, method_auth_requirement))

                ret = self.factory.methods[method](*args, **kwargs)
            except Exception, e:
                # Send an error packet here
                exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()

                self.sendData((
                    RPC_ERROR,
                    request_id,
                    (exceptionType.__name__,
                    exceptionValue.message,
                    "".join(traceback.format_tb(exceptionTraceback)))
                ))
                # Don't bother printing out DelugeErrors, because they are just for the client
                if not isinstance(e, DelugeError):
                    log.exception("Exception calling RPC request: %s", e)
            else:
                self.sendData((RPC_RESPONSE, request_id, ret))

class RPCServer(component.Component):
    """
    This class is used to handle rpc requests from the client.  Objects are
    registered with this class and their methods are exported using the export
    decorator.

    :param port: int, the port the RPCServer will listen on
    :param interface: str, the interface to listen on, this may override the `:param:allow_remote` setting
    :param allow_remote: bool, set True if the server should allow remote connections
    :param listen: bool, if False, will not start listening.. This is only useful in Classic Mode
    """

    def __init__(self, port=58846, interface="", allow_remote=False, listen=True):
        component.Component.__init__(self, "RPCServer")

        self.factory = Factory()
        self.factory.protocol = DelugeRPCProtocol
        # Holds the registered methods
        self.factory.methods = {}
        # Holds the session_ids and auth levels
        self.factory.authorized_sessions = {}

        if not listen:
            return

        if allow_remote:
            hostname = ""
        else:
            hostname = "localhost"

        if interface:
            hostname = interface

        log.info("Starting DelugeRPC server %s:%s", hostname, port)

        # Check for SSL cert/key and create them if necessary
        ssl_dir = deluge.configmanager.get_config_dir("ssl")
        if not os.path.exists(ssl_dir):
            # The ssl folder doesn't exist so we need to create it
            os.makedirs(ssl_dir)
            self.__generate_ssl_keys()
        else:
            for f in ("daemon.pkey", "daemon.cert"):
                if not os.path.exists(os.path.join(ssl_dir, f)):
                    self.__generate_ssl_keys()

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

        :param obj: object, the object that we want to export
        :param name: str, the name to use, if None, it will be the class name of the object
        """
        if not name:
            name = obj.__class__.__name__.lower()

        log.debug("dir: %s", dir(obj))
        for d in dir(obj):
            if d[0] == "_":
                continue
            if getattr(getattr(obj, d), '_rpcserver_export', False):
                log.debug("Registering method: %s", name + "." + d)
                #self.server.register_function(getattr(obj, d), name + "." + d)
                self.factory.methods[name + "." + d] = getattr(obj, d)

    def get_object_method(self, name):
        return self.factory.methods[name]

    def __generate_ssl_keys(self):
        """
        This method generates a new SSL key/cert.
        """
        digest = "md5"
        # Generate key pair
        pkey = crypto.PKey()
        pkey.generate_key(crypto.TYPE_RSA, 1024)

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
        cert.gmtime_adj_notAfter(60*60*24*365*5) # Five Years
        cert.set_issuer(req.get_subject())
        cert.set_subject(req.get_subject())
        cert.set_pubkey(req.get_pubkey())
        cert.sign(pkey, digest)

        # Write out files
        ssl_dir = deluge.configmanager.get_config_dir("ssl")
        open(os.path.join(ssl_dir, "daemon.pkey"), "w").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        open(os.path.join(ssl_dir, "daemon.cert"), "w").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        # Make the files only readable by this user
        for f in ("daemon.pkey", "daemon.cert"):
            os.chmod(os.path.join(ssl_dir, f), stat.S_IREAD | stat.S_IWRITE)
