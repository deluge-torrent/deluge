#
# client.py
#
# Copyright (C) 2007/2008 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
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


import os.path
import socket
import struct
import httplib
import urlparse

import gobject

import deluge.xmlrpclib as xmlrpclib

import deluge.common
import deluge.error
from deluge.log import LOG as log

class Transport(xmlrpclib.Transport):
    def __init__(self, username=None, password=None, use_datetime=0):
        self.__username = username
        self.__password = password
        self._use_datetime = use_datetime

    def request(self, host, handler, request_body, verbose=0):
        # issue XML-RPC request

        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)

        self.send_request(h, handler, request_body)
        self.send_host(h, host)
        self.send_user_agent(h)

        if self.__username is not None and self.__password is not None:
            h.putheader("AUTHORIZATION", "Basic %s" % string.replace(
                    encodestring("%s:%s" % (self.__username, self.__password)),
                    "\012", ""))

        self.send_content(h, request_body)

        errcode, errmsg, headers = h.getreply()

        if errcode != 200:
            raise xmlrpclib.ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
                )

        self.verbose = verbose

        try:
            sock = h._conn.sock
        except AttributeError:
            sock = None

        return self._parse_response(h.getfile(), sock)

    def make_connection(self, host):
        # create a HTTP connection object from a host descriptor
        import httplib
        host, extra_headers, x509 = self.get_host_info(host)
        h = httplib.HTTP(host)
        h._conn.connect()
        h._conn.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                      struct.pack('ii', 1, 0))
        return h

class CoreProxy(gobject.GObject):
    __gsignals__ = {
        "new_core" : (
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        "no_core" : (
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
    }
    def __init__(self):
        log.debug("CoreProxy init..")
        gobject.GObject.__init__(self)
        self._uri = None
        self.rpc_core = None
        self._multi = None
        self._callbacks = []
        self._multi_timer = None

    def call(self, func, callback, *args):
        if self.rpc_core is None or self._multi is None:
            if self.rpc_core is None:
                raise deluge.error.NoCoreError("The core proxy is invalid.")
                return
        _func = getattr(self._multi, func)

        if _func is not None:
            if (func, args) in self._multi.get_call_list():
                index = self._multi.get_call_list().index((func, args))
                if callback not in self._callbacks[index]:
                    self._callbacks[index].append(callback)
            else:
                if len(args) == 0:
                    _func()
                else:
                    _func(*args)

                self._callbacks.append([callback])

    def do_multicall(self, block=False):
        if len(self._callbacks) == 0:
            return True

        if self._multi is not None and self.rpc_core is not None:
            try:
                try:
                    for i, ret in enumerate(self._multi()):
                        try:
                            for callback in self._callbacks[i]:
                                if block == False:
                                    gobject.idle_add(callback, ret)
                                else:
                                    callback(ret)
                        except:
                            pass
                except (socket.error, xmlrpclib.ProtocolError), e:
                    log.error("Socket or XMLRPC error: %s", e)
                    self.set_core_uri(None)
                except (deluge.xmlrpclib.Fault, Exception), e:
                    #self.set_core_uri(None) , disabled : there are many reasons for an exception ; not just an invalid core.
                    #todo : publish an exception event, ui's like gtk could popup a dialog for this.
                    log.warning("Multi-call Exception: %s:%s", e, getattr(e,"message",None))
            finally:
                self._callbacks = []

        self._multi = xmlrpclib.MultiCall(self.rpc_core)

        return True

    def set_core_uri(self, uri):
        log.info("Setting core uri as %s", uri)

        if uri == None and self._uri != None:
            self._uri = None
            self.rpc_core = None
            self._multi = None
            try:
                gobject.source_remove(self._multi_timer)
            except:
                pass
            self.emit("no_core")
            return

        if uri != self._uri and self._uri != None:
            self.rpc_core = None
            self._multi = None
            try:
                gobject.source_remove(self._multi_timer)
            except:
                pass
            self.emit("no_core")

        self._uri = uri
        # Get a new core
        self.get_rpc_core()

    def get_core_uri(self):
        """Returns the URI of the core currently being used."""
        return self._uri

    def get_rpc_core(self):
        if self.rpc_core is None and self._uri is not None:
            log.debug("Creating ServerProxy..")
            self.rpc_core = xmlrpclib.ServerProxy(self._uri.replace("localhost", "127.0.0.1"), allow_none=True, transport=Transport())
            self._multi = xmlrpclib.MultiCall(self.rpc_core)
            self._multi_timer = gobject.timeout_add(200, self.do_multicall)
            # Call any callbacks registered
            self.emit("new_core")

        return self.rpc_core

_core = CoreProxy()

class BaseClient(object):
    """
    wraps all calls to core/coreproxy
    base for AClient and SClient
    """
    no_callback_list = ["add_torrent_url", "pause_all_torrents",
            "resume_all_torrents", "set_config", "enable_plugin",
            "disable_plugin", "set_torrent_trackers", "connect_peer",
            "set_torrent_max_connections", "set_torrent_max_upload_slots",
            "set_torrent_max_upload_speed", "set_torrent_max_download_speed",
            "set_torrent_private_flag", "set_torrent_file_priorities",
            "block_ip_range", "remove_torrent", "pause_torrent", "move_storage",
            "resume_torrent", "force_reannounce", "force_recheck",
            "deregister_client", "register_client", "add_torrent_file",
            "set_torrent_prioritize_first_last", "set_torrent_auto_managed",
            "set_torrent_stop_ratio", "set_torrent_stop_at_ratio",
            "set_torrent_remove_at_ratio", "set_torrent_move_on_completed",
            "set_torrent_move_on_completed_path", "add_torrent_magnets",
            "create_torrent", "upload_plugin", "rescan_plugins", "rename_files",
            "rename_folder"]

    def __init__(self):
        self.core = _core

    #xml-rpc introspection
    def list_methods(self):
        registered = self.core.rpc_core.system.listMethods()
        return sorted(registered)

    def methodSignature(self, method_name):
        "broken :("
        return self.core.rpc_core.system.methodSignature(method_name)

    def methodHelp(self, method_name):
        return self.core.rpc_core.system.methodHelp(method_name)

    #wrappers, getattr
    def get_method(self, method_name):
        "Override this in subclass."
        raise NotImplementedError()

    def __getattr__(self, method_name):
        return  self.get_method(method_name)
        #raise AttributeError("no attr/method named:%s" % attr)

    #custom wrapped methods:
    def add_torrent_file(self, torrent_files, torrent_options=None):
        """Adds torrent files to the core
        Expects a list of torrent files
        A list of torrent_option dictionaries in the same order of torrent_files
        """
        if torrent_files is None:
            log.debug("No torrent files selected..")
            return
        log.debug("Attempting to add torrent files: %s", torrent_files)
        for torrent_file in torrent_files:
            # Open the .torrent file for reading because we need to send it's
            # contents to the core.
            try:
                f = open(torrent_file, "rb")
            except Exception, e:
                log.warning("Unable to open %s: %s", torrent_file, e)
                continue

            # Get the name of the torrent from the TorrentInfo object because
            # it does better handling of encodings
            import deluge.ui.common
            ti = deluge.ui.common.TorrentInfo(torrent_file)
            filename = ti.name

            fdump = xmlrpclib.Binary(f.read())
            f.close()

            # Get the options for the torrent
            if torrent_options != None:
                try:
                    options = torrent_options[torrent_files.index(torrent_file)]
                except:
                    options = None
            else:
                options = None
            self.get_method("add_torrent_file")(filename, fdump, options)

    def add_torrent_file_binary(self, filename, fdump, options = None):
        """
        Core-wrapper.
        Adds 1 torrent file to the core.
        Expects fdump as a bytestring (== result of f.read()).
        """
        fdump_xmlrpc = xmlrpclib.Binary(fdump)
        self.get_method("add_torrent_file")(filename, fdump_xmlrpc, options)

    #utility:
    def has_callback(self, method_name):
        return not (method_name in self.no_callback_list)

    def is_localhost(self):
        """Returns True if core is a localhost"""
        # Get the uri
        uri = self.core.get_core_uri()
        if uri != None:
            # Get the host
            u = urlparse.urlsplit(uri)
            if u.hostname == "localhost" or u.hostname == "127.0.0.1":
                return True
        return False

    def get_core_uri(self):
        """Get the core URI"""
        return self.core.get_core_uri()

    def set_core_uri(self, uri='http://localhost:58846'):
        """Sets the core uri"""
        if uri:
            # Check if we need to get the localclient auth password
            u = urlparse.urlsplit(uri)
            if (u.hostname == "localhost" or u.hostname == "127.0.0.1") and not u.username:
                from deluge.ui.common import get_localhost_auth_uri
                uri = get_localhost_auth_uri(uri)
        return self.core.set_core_uri(uri)

    def connected(self):
        """Returns True if connected to a host, and False if not."""
        if self.get_core_uri() != None:
            return True
        return False

    def shutdown(self):
        """Shutdown the core daemon"""
        try:
            self.core.call("shutdown", None)
            self.core.do_multicall(block=False)
        finally:
            self.set_core_uri(None)

    #events:
    def connect_on_new_core(self, callback):
        """Connect a callback whenever a new core is connected to."""
        return self.core.connect("new_core", callback)

    def connect_on_no_core(self, callback):
        """Connect a callback whenever the core is disconnected from."""
        return self.core.connect("no_core", callback)

class SClient(BaseClient):
    """
    sync proxy
    """
    def get_method(self, method_name):
        return getattr(self.core.rpc_core, method_name)

class AClient(BaseClient):
    """
    async proxy
    """
    def get_method(self, method_name):
        if not self.has_callback(method_name):
            def async_proxy_nocb(*args, **kwargs):
                return self.core.call(method_name, None, *args, **kwargs)
            return async_proxy_nocb
        else:
            def async_proxy(*args, **kwargs):
                return self.core.call(method_name, *args, **kwargs)
            return async_proxy

    def force_call(self, block=True):
        """Forces the multicall batch to go now and not wait for the timer.  This
        call also blocks until all callbacks have been dealt with."""
        self.core.do_multicall(block=block)

sclient = SClient()
aclient = AClient()
