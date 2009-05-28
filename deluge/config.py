#
# config.py
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


"""
Deluge Config Module

This module is used for loading and saving of configuration files.. or anything
really.

The format of the config file is as follows:

<format version as int>
<config file version as int>
<content>

The format version is controlled by the Config class.  It should only be changed
when anything below it is changed directly by the Config class.  An example of
this would be if we changed the serializer for the content to something different.

The config file version is changed by the 'owner' of the config file.  This is
to signify that there is a change in the naming of some config keys or something
similar along those lines.

The content is simply the dict to be saved and will be serialized before being
written.

Converting

Since the format of the config could change, there needs to be a way to have
the Config object convert to newer formats.  To do this, you will need to
register conversion functions for various versions of the config file. Note that
this can only be done for the 'config file version' and not for the 'format'
version as this will be done internally.

"""

import cPickle as pickle
import shutil
import os

import deluge.common
from deluge.log import LOG as log

json = deluge.common.json

def prop(func):
    """Function decorator for defining property attributes

    The decorated function is expected to return a dictionary
    containing one or more of the following pairs:
        fget - function for getting attribute value
        fset - function for setting attribute value
        fdel - function for deleting attribute
    This can be conveniently constructed by the locals() builtin
    function; see:
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/205183
    """
    return property(doc=func.__doc__, **func())

class Config(object):
    """
    This class is used to access/create/modify config files

    :param filename: the name of the config file
    :param defaults: dictionary of default values
    :param config_dir: the path to the config directory

    """
    def __init__(self, filename, defaults=None, config_dir=None):
        self.__config = {}
        self.__set_functions = {}
        self.__change_callback = None

        # These hold the version numbers and they will be set when loaded
        self.__format_version = None
        self.__file_version = None

        # This will get set with a reactor.callLater whenever a config option
        # is set.
        self.__save_timer = None

        if defaults:
            self.__config = defaults

        # Load the config from file in the config_dir
        if config_dir:
            self.__config_file = os.path.join(config_dir, filename)
        else:
            self.__config_file = deluge.common.get_default_config_dir(filename)

        self.load()

    def __setitem__(self, key, value):
        """
        See
        :meth:`set_item`
        """

        return self.set_item(key, value)

    def set_item(self, key, value):
        """
        Sets item 'key' to 'value' in the config dictionary, but does not allow
        changing the item's type unless it is None

        :param key: string, item to change to change
        :param value: the value to change item to, must be same type as what is currently in the config

        :raises ValueError: raised when the type of value is not the same as what is currently in the config

        **Usage**

        >>> config = Config("test.conf")
        >>> config["test"] = 5
        >>> config["test"]
        5

        """
        if not self.__config.has_key(key):
            self.__config[key] = value
            log.debug("Setting '%s' to %s of %s", key, value, type(value))
            return

        if self.__config[key] == value:
            return

        # Do not allow the type to change unless it is None
        oldtype, newtype = type(self.__config[key]), type(value)

        if value is not None and oldtype != type(None) and oldtype != newtype:
            try:
                value = oldtype(value)
            except ValueError:
                log.warning("Type '%s' invalid for '%s'", newtype, key)
                raise

        log.debug("Setting '%s' to %s of %s", key, value, type(value))

        self.__config[key] = value
        # Run the set_function for this key if any
        from twisted.internet import reactor
        try:
            reactor.callLater(0, self.__set_functions[key], key, value)
        except KeyError:
            pass
        try:
            reactor.callLater(0, self.__change_callback, key, value)
        except:
            pass

        # We set the save_timer for 5 seconds if not already set
        if not self.__save_timer or not self.__save_timer.active():
            self.__save_timer = reactor.callLater(5, self.save)

    def __getitem__(self, key):
        """
        See
        :meth:`get_item`
        """
        return self.get_item(key)

    def get_item(self, key):
        """
        Gets the value of item 'key'

        :param key: the item for which you want it's value
        :return: the value of item 'key'

        :raises KeyError: if 'key' is not in the config dictionary

        **Usage**

        >>> config = Config("test.conf", defaults={"test": 5})
        >>> config["test"]
        5

        """
        return self.__config[key]

    def register_change_callback(self, callback):
        """
        Registers a callback function that will be called when a value is changed in the config dictionary

        :param callback: the function, callback(key, value)

        **Usage**

        >>> config = Config("test.conf", defaults={"test": 5})
        >>> def cb(key, value):
        ...     print key, value
        ...
        >>> config.register_change_callback(cb)

        """
        self.__change_callback = callback

    def register_set_function(self, key, function, apply_now=True):
        """
        Register a function to be called when a config value changes

        :param key: the item to monitor for change
        :param function: the function to call when the value changes, f(key, value)
        :keyword apply_now: if True, the function will be called after it's registered

        **Usage**

        >>> config = Config("test.conf", defaults={"test": 5})
        >>> def cb(key, value):
        ...     print key, value
        ...
        >>> config.register_set_function("test", cb, apply_now=True)
        test 5

        """
        log.debug("Registering function for %s key..", key)
        self.__set_functions[key] = function
        # Run the function now if apply_now is set
        if apply_now:
            self.__set_functions[key](key, self.__config[key])
        return

    def apply_all(self):
        """
        Calls all set functions

        **Usage**

        >>> config = Config("test.conf", defaults={"test": 5})
        >>> def cb(key, value):
        ...     print key, value
        ...
        >>> config.register_set_function("test", cb, apply_now=False)
        >>> config.apply_all()
        test 5

        """
        log.debug("Calling all set functions..")
        for key, value in self.__set_functions.iteritems():
            value(key, self.__config[key])

    def load(self, filename=None):
        """
        Load a config file

        :param filename: if None, uses filename set in object initialization


        """
        if not filename:
            filename = self.__config_file
        data = open(filename, "rb")
        try:
            self.__format_version = int(data.readline())
        except ValueError:
            pass

        try:
            self.__file_version = int(data.readline())
        except ValueError:
            pass


        if not self.__format_version:
            data.seek(0)
            self.__format_version = 1
            self.__file_version = 1

        fdata = data.read()
        data.close()

        try:
            self.__config.update(json.loads(fdata))
        except Exception, e:
            try:
                self.__config.update(pickle.loads(fdata))
            except Exception, e:
                log.exception(e)
                log.warning("Unable to load config file: %s", filename)



        log.debug("Config %s version: %s.%s loaded: %s", filename,
            self.__format_version, self.__file_version, self.__config)

    def save(self, filename=None):
        """
        Save configuration to disk

        :param filename: if None, uses filename set in object initiliazation
        :rtype bool:
        :return: whether or not the save succeeded.

        """
        if not filename:
            filename = self.__config_file
        # Check to see if the current config differs from the one on disk
        # We will only write a new config file if there is a difference
        try:
            data = open(filename, "rb")
            data.seek(2)
            loaded_data = json.load(data)
            data.close()
            if self.__config == loaded_data:
                # The config has not changed so lets just return
                self.__save_timer = None
                return
        except Exception, e:
            log.warning("Unable to open config file: %s", filename)

        self.__save_timer = None

        # Save the new config and make sure it's written to disk
        try:
            log.debug("Saving new config file %s", filename + ".new")
            f = open(filename + ".new", "wb")
            f.write(str(self.__format_version) + "\n")
            f.write(str(self.__file_version) + "\n")
            json.dump(self.__config, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
            f.close()
        except Exception, e:
            log.error("Error writing new config file: %s", e)
            return False

        # Make a backup of the old config
        try:
            log.debug("Backing up old config file to %s~", filename)
            shutil.move(filename, filename + "~")
        except Exception, e:
            log.error("Error backing up old config..")

        # The new config file has been written successfully, so let's move it over
        # the existing one.
        try:
            log.debug("Moving new config file %s to %s..", filename + ".new", filename)
            shutil.move(filename + ".new", filename)
        except Exception, e:
            log.error("Error moving new config file: %s", e)
            return False
        else:
            return True

    def run_converter(self, input_range, output_version, func):
        """
        Runs a function that will convert file versions in the `:param:input_range`
        to the `:param:output_version`.

        :param input_range: tuple, (int, int) the range of input versions this
            function will accept
        :param output_version: int, the version this function will return
        :param func: func, the function that will do the conversion, it will take
            the config dict as an argument and return the augmented dict

        :raises ValueError: if the output_version is less than the input_range

        """
        if output_version in input_range or output_version <= max(input_range):
            raise ValueError("output_version needs to be greater than input_range")

        if self.__file_version not in input_range:
            log.debug("File version %s is not in input_range %s, ignoring converter function..",
                self.__file_version, input_range)
            return

        try:
            self.__config = func(self.__config)
        except Exception, e:
            log.exception(e)
            log.error("There was an exception try to convert config file %s %s to %s",
                self.__config_file, self.__file_version, output_version)
            raise e
        else:
            self.__file_version = output_version
            self.save()

    @property
    def config_file(self):
        return self.__config_file

    @prop
    def config():
        """The config dictionary"""
        def fget(self):
            return self.__config
        def fdel(self):
            return self.save()
        return locals()
