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

The format of the config file is two json encoded dicts:

<version dict>
<content dict>

The version dict contains two keys: file and format.  The format version is
controlled by the Config class.  It should only be changed when anything below
it is changed directly by the Config class.  An example of this would be if we
changed the serializer for the content to something different.

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

from __future__ import with_statement

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

def find_json_objects(s):
    """
    Find json objects in a string.

    :param s: the string to find json objects in
    :type s: string

    :returns: a list of tuples containing start and end locations of json objects in the string `s`
    :rtype: [(start, end), ...]

    """
    objects = []
    opens = 0
    start = s.find("{")
    offset = start

    if start < 0:
        return []

    for index, c in enumerate(s[offset:]):
        if c == "{":
            opens += 1
        elif c == "}":
            opens -= 1
            if opens == 0:
                objects.append((start, index+offset+1))
                start = index + offset + 1

    return objects


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
        self.__change_callbacks = []

        # These hold the version numbers and they will be set when loaded
        self.__version = {
            "format": 1,
            "file": 1
        }

        # This will get set with a reactor.callLater whenever a config option
        # is set.
        self._save_timer = None

        if defaults:
            for key, value in defaults.iteritems():
                self.set_item(key, value)

        # Load the config from file in the config_dir
        if config_dir:
            self.__config_file = os.path.join(config_dir, filename)
        else:
            self.__config_file = deluge.common.get_default_config_dir(filename)

        self.load()

    def __contains__(self, item):
        return item in self.__config

    def __setitem__(self, key, value):
        """
        See
        :meth:`set_item`
        """

        return self.set_item(key, value)

    def set_item(self, key, value):
        """
        Sets item 'key' to 'value' in the config dictionary, but does not allow
        changing the item's type unless it is None.  If the types do not match,
        it will attempt to convert it to the set type before raising a ValueError.

        :param key: string, item to change to change
        :param value: the value to change item to, must be same type as what is currently in the config

        :raises ValueError: raised when the type of value is not the same as\
what is currently in the config and it could not convert the value

        **Usage**

        >>> config = Config("test.conf")
        >>> config["test"] = 5
        >>> config["test"]
        5

        """
        if isinstance(value, basestring):
            value = deluge.common.utf8_encoded(value)


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
                if oldtype == unicode:
                    value = oldtype(value, "utf8")
                else:
                    value = oldtype(value)
            except ValueError:
                log.warning("Type '%s' invalid for '%s'", newtype, key)
                raise

        log.debug("Setting '%s' to %s of %s", key, value, type(value))

        self.__config[key] = value
        # Run the set_function for this key if any
        from twisted.internet import reactor
        try:
            for func in self.__set_functions[key]:
                reactor.callLater(0, func, key, value)
        except KeyError:
            pass
        try:
            def do_change_callbacks(key, value):
                for func in self.__change_callbacks:
                    func(key, value)
            reactor.callLater(0, do_change_callbacks, key, value)
        except:
            pass

        # We set the save_timer for 5 seconds if not already set
        if not self._save_timer or not self._save_timer.active():
            self._save_timer = reactor.callLater(5, self.save)

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
        if isinstance(self.__config[key], str):
            try:
                return self.__config[key].decode("utf8")
            except UnicodeDecodeError:
                return self.__config[key]
        else:
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
        self.__change_callbacks.append(callback)

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
        if key not in self.__set_functions:
            self.__set_functions[key] = []

        self.__set_functions[key].append(function)

        # Run the function now if apply_now is set
        if apply_now:
            function(key, self.__config[key])
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
            for func in value:
                func(key, self.__config[key])

    def apply_set_functions(self, key):
        """
        Calls set functions for `:param:key`.

        :param key: str, the config key

        """
        log.debug("Calling set functions for key %s..", key)
        if key in self.__set_functions:
            for func in self.__set_functions[key]:
                func(key, self.__config[key])

    def load(self, filename=None):
        """
        Load a config file

        :param filename: if None, uses filename set in object initialization


        """
        if not filename:
            filename = self.__config_file

        try:
            with open(filename, "rb") as _file:
                data = _file.read()
        except IOError, e:
            log.warning("Unable to open config file %s: %s", filename, e)
            return

        objects = find_json_objects(data)

        if not len(objects):
            # No json objects found, try depickling it
            try:
                self.__config.update(pickle.loads(data))
            except Exception, e:
                log.exception(e)
                log.warning("Unable to load config file: %s", filename)
        elif len(objects) == 1:
            start, end = objects[0]
            try:
                self.__config.update(json.loads(data[start:end]))
            except Exception, e:
                log.exception(e)
                log.warning("Unable to load config file: %s", filename)
        elif len(objects) == 2:
            try:
                start, end = objects[0]
                self.__version.update(json.loads(data[start:end]))
                start, end = objects[1]
                self.__config.update(json.loads(data[start:end]))
            except Exception, e:
                log.exception(e)
                log.warning("Unable to load config file: %s", filename)

        log.debug("Config %s version: %s.%s loaded: %s", filename,
            self.__version["format"], self.__version["file"], self.__config)

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
            with open(filename, "rb") as _file:
                data = _file.read()
            objects = find_json_objects(data)
            start, end = objects[0]
            version = json.loads(data[start:end])
            start, end = objects[1]
            loaded_data = json.loads(data[start:end])
            if self.__config == loaded_data and self.__version == version:
                # The config has not changed so lets just return
                if self._save_timer and self._save_timer.active():
                    self._save_timer.cancel()
                return True
        except (IOError, IndexError), e:
            log.warning("Unable to open config file: %s because: %s", filename, e)

        # Save the new config and make sure it's written to disk
        try:
            log.debug("Saving new config file %s", filename + ".new")
            f = open(filename + ".new", "wb")
            json.dump(self.__version, f, indent=2)
            json.dump(self.__config, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
            f.close()
        except IOError, e:
            log.error("Error writing new config file: %s", e)
            return False

        # Make a backup of the old config
        try:
            log.debug("Backing up old config file to %s~", filename)
            shutil.move(filename, filename + "~")
        except Exception, e:
            log.warning("Unable to backup old config...")

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
        finally:
            if self._save_timer and self._save_timer.active():
                self._save_timer.cancel()

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

        if self.__version["file"] not in input_range:
            log.debug("File version %s is not in input_range %s, ignoring converter function..",
                self.__version["file"], input_range)
            return

        try:
            self.__config = func(self.__config)
        except Exception, e:
            log.exception(e)
            log.error("There was an exception try to convert config file %s %s to %s",
                self.__config_file, self.__version["file"], output_version)
            raise e
        else:
            self.__version["file"] = output_version
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
