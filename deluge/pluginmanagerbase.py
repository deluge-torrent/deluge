#
# pluginmanagerbase.py
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

"""PluginManagerBase"""

import os.path

import pkg_resources

import deluge.common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class PluginManagerBase:
    """PluginManagerBase is a base class for PluginManagers to inherit"""
    
    def __init__(self, config_file, entry_name):
        log.debug("Plugin manager init..")
        
        self.config = ConfigManager(config_file)
        
        # This is the entry we want to load..
        self.entry_name = entry_name
        
        # Loaded plugins
        self.plugins = {}
        
        # Scan the plugin folders for plugins
        self.scan_for_plugins()

        # Load plugins that are enabled in the config.
        for name in self.config["enabled_plugins"]:
            self.enable_plugin(name)
           
    def shutdown(self):
        log.debug("PluginManager shutting down..")
        for plugin in self.plugins.values():
            plugin.disable()
        del self.plugins
            
    def __getitem__(self, key):
        return self.plugins[key]
    
    def get_available_plugins(self):
        """Returns a list of the available plugins name"""
        return self.available_plugins
    
    def get_enabled_plugins(self):
        """Returns a list of enabled plugins"""
        return self.plugins.keys()
        
    def scan_for_plugins(self):
        """Scans for available plugins"""
        plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        user_plugin_dir = os.path.join(deluge.common.get_config_dir("plugins"))
        
        pkg_resources.working_set.add_entry(plugin_dir)
        pkg_resources.working_set.add_entry(user_plugin_dir)
        self.pkg_env = pkg_resources.Environment([plugin_dir, user_plugin_dir])

        self.available_plugins = []
        for name in self.pkg_env:
            pkg_name = str(self.pkg_env[name][0]).split()[0]
            pkg_version = str(self.pkg_env[name][0]).split()[1]
            
            log.debug("Found plugin: %s %s", pkg_name, pkg_version)
            self.available_plugins.append(pkg_name)

    def enable_plugin(self, name):
        """Enables a plugin"""
        if name not in self.available_plugins:
            log.warning("Cannot enable non-existant plugin %s", name)
            return
            
        egg = self.pkg_env[name][0]
        egg.activate()
        for name in egg.get_entry_map(self.entry_name):
            entry_point = egg.get_entry_info(self.entry_name, name)
            cls = entry_point.load()
            instance = cls(self)
            self.plugins[name] = instance
            log.info("Plugin %s enabled..", name)
            
    def disable_plugin(self, name):
        """Disables a plugin"""

        self.plugins[name].disable()
            
        del self.plugins[name]
#        except:
 #           log.warning("Unable to disable non-existant plugin %s", name)
        
        log.info("Plugin %s disabled..", name)
