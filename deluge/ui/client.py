#
# functions.py
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

import deluge.xmlrpclib as xmlrpclib

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade

import deluge.common
from deluge.log import LOG as log

class CoreProxy:
    def __init__(self):
        self._uri = None
        self._core = None
        self._on_new_core_callbacks = []
        self._on_no_core_callbacks = []
            
    def connect_on_new_core(self, callback):
        """Connect a callback to be called when a new core is connected to."""
        self._on_new_core_callbacks.append(callback)
    
    def connect_on_no_core(self, callback):
        """Connect a callback to be called when the current core is disconnected
        from."""
        self._on_no_core_callbacks.append(callback)
            
    def set_core_uri(self, uri):
        log.info("Setting core uri as %s", uri)

        if uri == None and self._uri != None:
            for callback in self._on_no_core_callbacks:
                callback()
            self._uri = None
            self._core = None
            return

        self._uri = uri
        # Get a new core
        self.get_core()
    
    def get_core_uri(self):
        """Returns the URI of the core currently being used."""
        return self._uri
            
    def get_core(self):
        if self._core is None and self._uri is not None:
            log.debug("Creating ServerProxy..")
            self._core = xmlrpclib.ServerProxy(self._uri)
            # Call any callbacks registered
            for callback in self._on_new_core_callbacks:
                callback()
        
        return self._core
               
_core = CoreProxy()

def get_core():
    """Get the core object and return it"""
    return _core.get_core()
    
def get_core_plugin(plugin):
    """Get the core plugin object and return it"""
    log.debug("Getting core plugin %s from DBUS..", plugin)
    bus = dbus.SessionBus()
    proxy = bus.get_object("org.deluge_torrent.Deluge", 
                               "/org/deluge_torrent/Plugin/" + plugin)
    core = dbus.Interface(proxy, "org.deluge_torrent.Deluge." + plugin)
    return core

def connect_on_new_core(callback):
    """Connect a callback whenever a new core is connected to."""
    return _core.connect_on_new_core(callback)

def connect_on_no_core(callback):
    """Connect a callback whenever the core is disconnected from."""
    return _core.connect_on_no_core(callback)
    
def set_core_uri(uri):
    """Sets the core uri"""
    return _core.set_core_uri(uri)

def get_core_uri():
    """Get the core URI"""
    return _core.get_core_uri()
        
def shutdown():
    """Shutdown the core daemon"""
    try:
        get_core().shutdown()
    except (AttributeError, socket.error):
        set_core_uri(None)
     
def add_torrent_file(torrent_files):
    """Adds torrent files to the core
        Expects a list of torrent files
    """
    if torrent_files is None:
        log.debug("No torrent files selected..")
        return
    log.debug("Attempting to add torrent files: %s", torrent_files)
    for torrent_file in torrent_files:
        # Open the .torrent file for reading because we need to send it's
        # contents to the core.
        f = open(torrent_file, "rb")
        # Get the filename because the core doesn't want a path.
        (path, filename) = os.path.split(torrent_file)
        fdump = xmlrpclib.Binary(f.read())
        f.close()
        try:
            result = get_core().add_torrent_file(filename, str(), fdump)
        except (AttributeError, socket.error):
            set_core_uri(None)
            result = False
            
        if result is False:
            # The torrent was not added successfully.
            log.warning("Torrent %s was not added successfully.", filename)

def add_torrent_url(torrent_url):
    """Adds torrents to the core via url"""
    from deluge.common import is_url
    if is_url(torrent_url):
        try:
            result = get_core().add_torrent_url(torrent_url, str())
        except (AttributeError, socket.error):
            set_core_uri(None)
            result = False
            
        if result is False:
            # The torrent url was not added successfully.
            log.warning("Torrent %s was not added successfully.", torrent_url)
    else:
        log.warning("Invalid URL %s", torrent_url)
    
def remove_torrent(torrent_ids):
    """Removes torrent_ids from the core.. Expects a list of torrent_ids"""
    log.debug("Attempting to removing torrents: %s", torrent_ids)
    try:
        for torrent_id in torrent_ids:
            get_core().remove_torrent(torrent_id)
    except (AttributeError, socket.error):
        set_core_uri(None)

def pause_torrent(torrent_ids):
    """Pauses torrent_ids"""
    try:
        for torrent_id in torrent_ids:
            get_core().pause_torrent(torrent_id)
    except (AttributeError, socket.error):
        set_core_uri(None)

def resume_torrent(torrent_ids):
    """Resume torrent_ids"""
    try:
        for torrent_id in torrent_ids:
            get_core().resume_torrent(torrent_id)
    except (AttributeError, socket.error):
        set_core_uri(None)
        
def force_reannounce(torrent_ids):
    """Reannounce to trackers"""
    try:
        for torrent_id in torrent_ids:
            get_core().force_reannounce(torrent_id)
    except (AttributeError, socket.error):
        set_core_uri(None)

def get_torrent_status(torrent_id, keys):
    """Builds the status dictionary and returns it"""
    try:
        status = get_core().get_torrent_status(torrent_id, keys)
    except (AttributeError, socket.error):
        set_core_uri(None)
        return {}
    return pickle.loads(status.data)
    
def get_session_state():
    try:
        state = get_core().get_session_state()
    except (AttributeError, socket.error):
        set_core_uri(None)
        state = []
    return state
    
def get_config():
    try:
        config = get_core().get_config()
    except (AttributeError, socket.error):
        set_core_uri(None)
        config = {}
    return config
    
def get_config_value(key):
    try:
        config_value = get_core().get_config_value(key)
    except (AttributeError, socket.error):
        set_core_uri(None)
        config_value = None
    return config_value
    
def set_config(config):
    if config == {}:
        return
    try:
        get_core().set_config(config)
    except (AttributeError, socket.error):
        set_core_uri(None)
    
def get_listen_port():
    try:
        port = get_core().get_listen_port()
    except (AttributeError, socket.error):
        set_core_uri(None)
        port = 0
    return int(port)

def get_available_plugins():
    try:
        available = get_core().get_available_plugins()
    except (AttributeError, socket.error):
        set_core_uri(None)
        available = []
    return available
    
def get_enabled_plugins():
    try:
        enabled = get_core().get_enabled_plugins()
    except (AttributeError, socket.error):
        set_core_uri(None)
        enabled = []
    return enabled
    
def get_download_rate():
    try:
        rate = get_core().get_download_rate()
    except (AttributeError, socket.error):
        set_core_uri(None)
        rate = -1
    return rate
    
def get_upload_rate():
    try:
        rate = get_core().get_upload_rate()
    except (AttributeError, socket.error):
        set_core_uri(None)
        rate = -1
    return rate

def get_num_connections():
    try:
        num_connections = get_core().get_num_connections()
    except (AttributeError, socket.error):
        set_core_uri(None)
        num_connections = 0
    return num_connections
        
def open_url_in_browser(url):
    """Opens link in the desktop's default browser"""
    def start_browser():
        import webbrowser
        log.debug("Opening webbrowser with url: %s", url)
        webbrowser.open(url)
        return False
        
    import gobject
    gobject.idle_add(start_browser)
