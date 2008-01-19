#
# client.py
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

import os.path
import pickle
import socket
import time

import gobject

import deluge.xmlrpclib as xmlrpclib

import deluge.common
from deluge.log import LOG as log

CACHE_TTL = 1.5 # seconds

class cache:
    def __init__(self, func):
        self.func = func

        #self.cache_values = {(args, kwargs): (time, ret)}
        self.cache_values = {}
        
    def __call__(self, *__args, **__kw):
        # Turn the arguments into hashable values
        if __args == ():
            args = None
        else:
            args = __args
        
        if __kw == {}:
            kw = None
        else:
            kw = __kw
            
        # See if there is a cached return value for this call
        if self.cache_values.has_key((args, kw)):
            # Check the timestamp on the value to ensure it's still valid
            if time.time() - self.cache_values[(args, kw)][0] < CACHE_TTL:
                return self.cache_values[(args, kw)][1]
        
        # No return value in cache
        ret = self.func(*__args, **__kw)
        self.cache_values[(args, kw)] = [time.time(), ret]
        return ret

class cache_dict:
    """Special cache decorator for get_torrent_status and the like.. It expects
    passing a str, list and returns a dict"""
    def __init__(self, func):
        self.func = func
        self.cache_values = {}
    
    def __call__(self, *__args, **__kw):
        if __args == ():
            return
        # Check for a cache value for these parameters
        if self.cache_values.has_key(__args[0]):
            # Check the timestamp on the value to ensure it's still valid
            if time.time() - self.cache_values[__args[0]][0] < CACHE_TTL:
                # Check to see if we have the right keys in cache
                cache_dict = self.cache_values[__args[0]][1]
                if cache_dict == None:
                    cache_dict = {}
                keys = __args[1]
                non_cached = []
                ret_dict = {}
                for key in keys:
                    if key in cache_dict.keys():
                        ret_dict[key] = cache_dict[key]
                    else:
                        non_cached.append(key)
                
                # If there aren't any non_cached keys then lets just return
                # cached values
                if len(non_cached) == 0:
                    return ret_dict
        
                # We need to request the remaining non-cached keys from the func
                ret = self.func(*(__args[0], non_cached), **__kw)
                if ret == None:
                    return ret
                ret.update(ret_dict)
                self.cache_values[__args[0]] = [time.time(), ret]
                return ret
                
        # Not cached
        ret = self.func(*__args, **__kw)
        self.cache_values[__args[0]] = [time.time(), ret]
        return ret                    
                            
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
        self._core = None
        self._multi = None
        self._callbacks = []
        gobject.timeout_add(10, self.do_multicall)

    def call(self, func, callback, *args):
        if self._core is None or self._multi is None:
            if self.get_core() is None:
                return
        _func = getattr(self._multi, func)

        if _func is not None:
            if len(args) == 0:
                _func()
            else:
                _func(*args)
        self._callbacks.append(callback)


    def do_multicall(self, block=False):
        if len(self._callbacks) == 0:
            return True
            
        if self._multi is not None:
            try:
                for i, ret in enumerate(self._multi()):
                    try:
                        if block == False:
                            gobject.idle_add(self._callbacks[i], ret)
                        else:
                            self._callbacks[i](ret)
                    except:
                        pass
            except socket.error, e:
                log.warning("Could not contact daemon: %s", e)
                self.set_core_uri(None)
            finally:                        
                self._callbacks = []
                
        self._multi = xmlrpclib.MultiCall(self._core)
        return True
        
    def set_core_uri(self, uri):
        log.info("Setting core uri as %s", uri)
        
        if uri == None and self._uri != None:
            self.emit("no_core")
            self._uri = None
            self._core = None
            return
        
        if uri != self._uri and self._uri != None:
            self._core = None
            self.emit("no_core")
                            
        self._uri = uri
        # Get a new core
        self.get_core()
    
    def get_core_uri(self):
        """Returns the URI of the core currently being used."""
        return self._uri
            
    def get_core(self):
        if self._core is None and self._uri is not None:
            log.debug("Creating ServerProxy..")
            self._core = xmlrpclib.ServerProxy(self._uri, allow_none=True)
            self._multi = xmlrpclib.MultiCall(self._core)
            # Call any callbacks registered
            self.emit("new_core")
        
        return self._core
                      
_core = CoreProxy()

def get_core():
    """Get the core object and return it"""
    return _core
    
def connect_on_new_core(callback):
    """Connect a callback whenever a new core is connected to."""
    return _core.connect("new_core", callback)

def connect_on_no_core(callback):
    """Connect a callback whenever the core is disconnected from."""
    return _core.connect("no_core", callback)
  
def set_core_uri(uri):
    """Sets the core uri"""
    return _core.set_core_uri(uri)

def get_core_uri():
    """Get the core URI"""
    return _core.get_core_uri()

def is_localhost():
    """Returns True if core is a localhost"""
    # Get the uri
    uri = _core.get_core_uri()
    if uri != None:
        # Get the host
        host = uri[7:].split(":")[0]
        if host == "localhost" or host == "127.0.0.1":
            return True
    
    return False

def connected():
    """Returns True if connected to a host, and False if not."""
    if get_core_uri() != None:
        return True
    return False

def register_client(port):
    get_core().call("register_client", None, port)

def deregister_client():
    get_core().call("deregister_client", None)
                
def shutdown():
    """Shutdown the core daemon"""
    try:
        get_core().call("shutdown", None)
        force_call(block=False)
    except:
        # Ignore everything
        set_core_uri(None)

def force_call(block=True):
    """Forces the multicall batch to go now and not wait for the timer.  This
    call also blocks until all callbacks have been dealt with."""
    get_core().do_multicall(block=block)
       
def add_torrent_file(torrent_files, torrent_options=None):
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
            
        # Get the filename because the core doesn't want a path.
        (path, filename) = os.path.split(torrent_file)
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
            
        get_core().call("add_torrent_file", None,
            filename, str(), fdump, options)

def add_torrent_url(torrent_url, options=None):
    """Adds torrents to the core via url"""
    from deluge.common import is_url
    if is_url(torrent_url):
        get_core().call("add_torrent_url", None, 
            torrent_url, str(), options)
    else:
        log.warning("Invalid URL %s", torrent_url)
    
def remove_torrent(torrent_ids, remove_torrent=False, remove_data=False):
    """Removes torrent_ids from the core.. Expects a list of torrent_ids"""
    log.debug("Attempting to removing torrents: %s", torrent_ids)
    for torrent_id in torrent_ids:
        get_core().call("remove_torrent", None, torrent_id, remove_torrent, remove_data)

def pause_torrent(torrent_ids):
    """Pauses torrent_ids"""
    for torrent_id in torrent_ids:
        get_core().call("pause_torrent", None, torrent_id)

def pause_all_torrents():
    """Pauses all torrents"""
    get_core().call("pause_all_torrents", None)

def resume_all_torrents():
    """Resumes all torrents"""
    get_core().call("resume_all_torrents", None)
        
def resume_torrent(torrent_ids):
    """Resume torrent_ids"""
    for torrent_id in torrent_ids:
        get_core().call("resume_torrent", None, torrent_id)
        
def force_reannounce(torrent_ids):
    """Reannounce to trackers"""
    for torrent_id in torrent_ids:
        get_core().call("force_reannounce", None, torrent_id)

def get_torrent_status(callback, torrent_id, keys):
    """Builds the status dictionary and returns it"""
    get_core().call("get_torrent_status", callback, torrent_id, keys)

def get_torrents_status(callback, torrent_ids, keys):
    """Builds a dictionary of torrent_ids status.  Expects 2 lists.  This is
    asynchronous so the return value will be sent as the signal
    'torrent_status'"""
    get_core().call("get_torrents_status", callback, torrent_ids, keys)

def get_session_state(callback):
    get_core().call("get_session_state", callback)

def get_config(callback):
    get_core().call("get_config", callback)

def get_config_value(callback, key):
    get_core().call("get_config_value", callback, key)
    
def set_config(config):
    if config == {}:
        return
    get_core().call("set_config", None, config)

def get_listen_port(callback):
    get_core().call("get_listen_port", callback)

def get_available_plugins(callback):
    get_core().call("get_available_plugins", callback)

def get_enabled_plugins(callback):
    get_core().call("get_enabled_plugins", callback)

def get_download_rate(callback):
    get_core().call("get_download_rate", callback)

def get_upload_rate(callback):
    get_core().call("get_upload_rate", callback)

def get_num_connections(callback):
    get_core().call("get_num_connections", callback)

def enable_plugin(plugin):
    get_core().call("enable_plugin", None, plugin)
            
def disable_plugin(plugin):
    get_core().call("disable_plugin", None, plugin)

def force_recheck(torrent_ids):
    """Forces a data recheck on torrent_ids"""
    for torrent_id in torrent_ids:
        get_core().call("force_recheck", None, torrent_id)

def set_torrent_trackers(torrent_id, trackers):
    """Sets the torrents trackers"""
    get_core().call("set_torrent_trackers", None, torrent_id, trackers)

