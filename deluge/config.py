#
# config.py
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

"""Configuration class used to access/create/modify configuration files."""

import cPickle

import gobject
import deluge.common
from deluge.log import LOG as log

class Config:
    """This class is used to access configuration files."""
    
    def __init__(self, filename, defaults=None):
        log.debug("Config created with filename: %s", filename)
        log.debug("Config defaults: %s", defaults)
        self.config = {}
        self.set_functions = {}
        
        # If defaults is not None then we need to use "defaults".
        if defaults != None:
            self.config = defaults

        # Load the config from file in the config_dir
        self.config_file = deluge.common.get_config_dir(filename)
        self.load(self.config_file)
        # Save
        self.save()
        
    def __del__(self):
        log.debug("Config object deconstructing..")
        self.save()
            
    def load(self, filename=None):
        """Load a config file either by 'filename' or the filename set during
        construction of this object."""
        # Use self.config_file if filename is None
        if filename is None:
            filename = self.config_file
        try:
            # Un-pickle the file and update the config dictionary
            log.debug("Opening pickled file for load..")
            pkl_file = open(filename, "rb")
            filedump = cPickle.load(pkl_file)
            self.config.update(filedump)
            pkl_file.close()
        except IOError:
            log.warning("IOError: Unable to load file '%s'", filename)
        except EOFError:
            log.debug("Closing pickled file..")
            pkl_file.close()
            
    def save(self, filename=None):
        """Save configuration to either 'filename' or the filename set during
        construction of this object."""
        # Saves the config dictionary
        if filename is None:
            filename = self.config_file
        # Check to see if the current config differs from the one on disk
        # We will only write a new config file if there is a difference
        try:
            log.debug("Opening pickled file for comparison..")
            pkl_file = open(filename, "rb")
            filedump = cPickle.load(pkl_file)
            pkl_file.close()
            if filedump == self.config:
                # The config has not changed so lets just return
                log.debug("Not writing config file due to no changes..")
                return
        except IOError:
            log.warning("IOError: Unable to open file: '%s'", filename)
            
        try:
            log.debug("Opening pickled file for save..")
            pkl_file = open(filename, "wb")
            cPickle.dump(self.config, pkl_file)
            log.debug("Closing pickled file..")
            pkl_file.close()
        except IOError:
            log.warning("IOError: Unable to save file '%s'", filename)
            
    def set(self, key, value):
        """Set the 'key' with 'value'."""
	    # Sets the "key" with "value" in the config dict
        if self.config[key] != value:
            log.debug("Setting '%s' to %s of %s", key, value, type(value))
            self.config[key] = value
            # Run the set_function for this key if any
            try:
                self.set_functions[key](key, value)
            except KeyError:
                pass

    def get(self, key):
        """Get the value of 'key'.  If it is an invalid key then get() will
        return None."""
        # Attempts to get the "key" value and returns None if the key is 
        # invalid
        try:
            value = self.config[key]
            log.debug("Getting '%s' as %s of %s", key, value, type(value))
            return value
        except KeyError:
            log.warning("Key does not exist, returning None")
            return None

    def get_config(self):
        """Returns the entire configuration as a dictionary."""
        return self.config
    
    def register_set_function(self, key, function, apply_now=True):
        """Register a function to be run when a config value changes."""
        log.debug("Registering function for %s key..", key)
        self.set_functions[key] = function
        # Run the function now if apply_now is set
        if apply_now:
            self.set_functions[key](key, self.config[key])
        return
    
    def apply_all(self):
        """Runs all set functions"""
        log.debug("Running all set functions..")
        for key in self.set_functions.keys():
            self.set_functions[key](key, self.config[key])
                    
    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.set(key, value)

