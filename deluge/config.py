#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
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
import json
import logging
import os
import pickle
import shutil
from codecs import getwriter
from tempfile import NamedTemporaryFile

from deluge.common import JSON_FORMAT, get_default_config_dir

log = logging.getLogger(__name__)


def find_json_objects(text, decoder=json.JSONDecoder()):
    """Find json objects in text.

    Args:
        text (str): The text to find json objects within.

    Returns:
        list: A list of tuples containing start and end locations of json
            objects in the text. e.g. [(start, end), ...]


    """
    objects = []
    offset = 0
    while True:
        try:
            start = text.index('{', offset)
        except ValueError:
            break

        try:
            __, index = decoder.raw_decode(text[start:])
        except json.decoder.JSONDecodeError:
            offset = start + 1
        else:
            offset = start + index
            objects.append((start, offset))

    return objects


def cast_to_existing_type(value, old_value):
    """Attempt to convert new value type to match old value type"""
    types_match = isinstance(old_value, (type(None), type(value)))
    if value is not None and not types_match:
        old_type = type(old_value)
        # Skip convert to bytes since requires knowledge of encoding and value should
        # be unicode anyway.
        if old_type is bytes:
            return value

        return old_type(value)

    return value


class Config:
    """This class is used to access/create/modify config files.

    Args:
        filename (str): The config filename.
        defaults (dict): The default config values to insert before loading the config file.
        config_dir (str): the path to the config directory.
        file_version (int): The file format for the default config values when creating
            a fresh config. This value should be increased whenever a new migration function is
            setup to convert old config files. (default: 1)
        log_mask_funcs (dict): A dict of key:function, used to mask sensitive
            key values (e.g. passwords) when logging is enabled.

    """

    def __init__(
        self,
        filename,
        defaults=None,
        config_dir=None,
        file_version=1,
        log_mask_funcs=None,
    ):
        self.__config = {}
        self.__set_functions = {}
        self.__change_callbacks = []
        self.__log_mask_funcs = log_mask_funcs if log_mask_funcs else {}

        # These hold the version numbers and they will be set when loaded
        self.__version = {'format': 1, 'file': file_version}

        # This will get set with a reactor.callLater whenever a config option
        # is set.
        self._save_timer = None

        if defaults:
            for key, value in defaults.items():
                self.set_item(key, value, default=True)

        # Load the config from file in the config_dir
        if config_dir:
            self.__config_file = os.path.join(config_dir, filename)
        else:
            self.__config_file = get_default_config_dir(filename)

        self.load()

    def callLater(self, period, func, *args, **kwargs):  # noqa: N802 ignore camelCase
        """Wrapper around reactor.callLater for test purpose."""
        from twisted.internet import reactor

        return reactor.callLater(period, func, *args, **kwargs)

    def __contains__(self, item):
        return item in self.__config

    def __setitem__(self, key, value):
        """See set_item"""

        return self.set_item(key, value)

    def set_item(self, key, value, default=False):
        """Sets item 'key' to 'value' in the config dictionary.

        Does not allow changing the item's type unless it is None.

        If the types do not match, it will attempt to convert it to the
        set type before raising a ValueError.

        Args:
            key (str): Item to change to change.
            value (any): The value to change item to, must be same type as what is
                currently in the config.
            default (optional, bool): When setting a default value skip func or save
                callbacks.

        Raises:
            ValueError: Raised when the type of value is not the same as what is
                currently in the config and it could not convert the value.

        Examples:
            >>> config = Config('test.conf')
            >>> config['test'] = 5
            >>> config['test']
            5

        """
        if isinstance(value, bytes):
            value = value.decode()

        if key in self.__config:
            try:
                value = cast_to_existing_type(value, self.__config[key])
            except ValueError:
                log.warning('Value Type "%s" invalid for key: %s', type(value), key)
                raise
            else:
                if self.__config[key] == value:
                    return

        if log.isEnabledFor(logging.DEBUG):
            if key in self.__log_mask_funcs:
                value = self.__log_mask_funcs[key](value)
            log.debug(
                'Setting key "%s" to: %s (of type: %s)',
                key,
                value,
                type(value),
            )
        self.__config[key] = value

        # Skip save or func callbacks if setting default value for keys
        if default:
            return

        # Run the set_function for this key if any
        for func in self.__set_functions.get(key, []):
            self.callLater(0, func, key, value)

        try:

            def do_change_callbacks(key, value):
                for func in self.__change_callbacks:
                    func(key, value)

            self.callLater(0, do_change_callbacks, key, value)
        except Exception:
            pass

        # We set the save_timer for 5 seconds if not already set
        if not self._save_timer or not self._save_timer.active():
            self._save_timer = self.callLater(5, self.save)

    def __getitem__(self, key):
        """See get_item"""
        return self.get_item(key)

    def get_item(self, key):
        """Gets the value of item 'key'.

        Args:
            key (str): The item for which you want it's value.

        Returns:
            any: The value of item 'key'.

        Raises:
            ValueError: If 'key' is not in the config dictionary.

        Examples:
            >>> config = Config('test.conf', defaults={'test': 5})
            >>> config['test']
            5

        """
        return self.__config[key]

    def get(self, key, default=None):
        """Gets the value of item 'key' if key is in the config, else default.

        If default is not given, it defaults to None, so that this method
        never raises a KeyError.

        Args:
            key (str): the item for which you want it's value
            default (any): the default value if key is missing

        Returns:
            any: The value of item 'key' or default.

        Examples:
            >>> config = Config('test.conf', defaults={'test': 5})
            >>> config.get('test', 10)
            5
            >>> config.get('bad_key', 10)
            10

        """
        try:
            return self.get_item(key)
        except KeyError:
            return default

    def __delitem__(self, key):
        """
        See
        :meth:`del_item`
        """
        self.del_item(key)

    def del_item(self, key):
        """Deletes item with a specific key from the configuration.

        Args:
            key (str): The item which you wish to delete.

        Raises:
            ValueError: If 'key' is not in the config dictionary.

        Examples:
            >>> config = Config('test.conf', defaults={'test': 5})
            >>> del config['test']

        """

        del self.__config[key]

        # We set the save_timer for 5 seconds if not already set
        if not self._save_timer or not self._save_timer.active():
            self._save_timer = self.callLater(5, self.save)

    def register_change_callback(self, callback):
        """Registers a callback function for any changed value.

        Will be called when any value is changed in the config dictionary.

        Args:
            callback (func): The function to call with parameters: f(key, value).

        Examples:
            >>> config = Config('test.conf', defaults={'test': 5})
            >>> def cb(key, value):
            ...     print key, value
            ...
            >>> config.register_change_callback(cb)

        """
        self.__change_callbacks.append(callback)

    def register_set_function(self, key, function, apply_now=True):
        """Register a function to be called when a config value changes.

        Args:
            key (str): The item to monitor for change.
            function (func): The function to call when the value changes, f(key, value).
            apply_now (bool): If True, the function will be called immediately after it's registered.

        Examples:
            >>> config = Config('test.conf', defaults={'test': 5})
            >>> def cb(key, value):
            ...     print key, value
            ...
            >>> config.register_set_function('test', cb, apply_now=True)
            test 5

        """
        log.debug('Registering function for %s key..', key)
        if key not in self.__set_functions:
            self.__set_functions[key] = []

        self.__set_functions[key].append(function)

        # Run the function now if apply_now is set
        if apply_now:
            function(key, self.__config[key])

    def apply_all(self):
        """Calls all set functions.

        Examples:
            >>> config = Config('test.conf', defaults={'test': 5})
            >>> def cb(key, value):
            ...     print key, value
            ...
            >>> config.register_set_function('test', cb, apply_now=False)
            >>> config.apply_all()
            test 5

        """
        log.debug('Calling all set functions..')
        for key, value in self.__set_functions.items():
            for func in value:
                func(key, self.__config[key])

    def apply_set_functions(self, key):
        """Calls set functions for `:param:key`.

        Args:
            key (str): the config key

        """
        log.debug('Calling set functions for key %s..', key)
        if key in self.__set_functions:
            for func in self.__set_functions[key]:
                func(key, self.__config[key])

    def load(self, filename=None):
        """Load a config file.

        Args:
            filename (str): If None, uses filename set in object initialization

        """
        if not filename:
            filename = self.__config_file

        try:
            with open(filename, encoding='utf8') as _file:
                data = _file.read()
        except OSError as ex:
            log.warning('Unable to open config file %s: %s', filename, ex)
            return

        objects = find_json_objects(data)

        if not len(objects):
            # No json objects found, try depickling it
            try:
                self.__config.update(pickle.loads(data))
            except Exception as ex:
                log.exception(ex)
                log.warning('Unable to load config file: %s', filename)
        elif len(objects) == 1:
            start, end = objects[0]
            try:
                self.__config.update(json.loads(data[start:end]))
            except Exception as ex:
                log.exception(ex)
                log.warning('Unable to load config file: %s', filename)
        elif len(objects) == 2:
            try:
                start, end = objects[0]
                self.__version.update(json.loads(data[start:end]))
                start, end = objects[1]
                self.__config.update(json.loads(data[start:end]))
            except Exception as ex:
                log.exception(ex)
                log.warning('Unable to load config file: %s', filename)

        if not log.isEnabledFor(logging.DEBUG):
            return

        config = self.__config
        if self.__log_mask_funcs:
            config = {
                key: self.__log_mask_funcs[key](config[key])
                if key in self.__log_mask_funcs
                else config[key]
                for key in config
            }

        log.debug(
            'Config %s version: %s.%s loaded: %s',
            filename,
            self.__version['format'],
            self.__version['file'],
            config,
        )

    def save(self, filename=None):
        """Save configuration to disk.

        Args:
            filename (str): If None, uses filename set in object initialization

        Returns:
            bool: Whether or not the save succeeded.

        """
        if not filename:
            filename = self.__config_file
        # Check to see if the current config differs from the one on disk
        # We will only write a new config file if there is a difference
        try:
            with open(filename, encoding='utf8') as _file:
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
        except (OSError, IndexError) as ex:
            log.warning('Unable to open config file: %s because: %s', filename, ex)

        # Save the new config and make sure it's written to disk
        try:
            with NamedTemporaryFile(
                prefix=os.path.basename(filename) + '.', delete=False
            ) as _file:
                filename_tmp = _file.name
                log.debug('Saving new config file %s', filename_tmp)
                json.dump(self.__version, getwriter('utf8')(_file), **JSON_FORMAT)
                json.dump(self.__config, getwriter('utf8')(_file), **JSON_FORMAT)
                _file.flush()
                os.fsync(_file.fileno())
        except OSError as ex:
            log.error('Error writing new config file: %s', ex)
            return False

        # Resolve symlinked config files before backing up and saving.
        filename = os.path.realpath(filename)

        # Make a backup of the old config
        try:
            log.debug('Backing up old config file to %s.bak', filename)
            shutil.move(filename, filename + '.bak')
        except OSError as ex:
            log.warning('Unable to backup old config: %s', ex)

        # The new config file has been written successfully, so let's move it over
        # the existing one.
        try:
            log.debug('Moving new config file %s to %s', filename_tmp, filename)
            shutil.move(filename_tmp, filename)
        except OSError as ex:
            log.error('Error moving new config file: %s', ex)
            return False
        else:
            return True
        finally:
            if self._save_timer and self._save_timer.active():
                self._save_timer.cancel()

    def run_converter(self, input_range, output_version, func):
        """Runs a function that will convert file versions.

        Args:
            input_range (tuple): (int, int) The range of input versions this function will accept.
            output_version (int): The version this function will convert to.
            func (func): The function that will do the conversion, it will take the config
                dict as an argument and return the augmented dict.

        Raises:
            ValueError: If output_version is less than the input_range.

        """
        if output_version in input_range or output_version <= max(input_range):
            raise ValueError('output_version needs to be greater than input_range')

        if self.__version['file'] not in input_range:
            log.debug(
                'File version %s is not in input_range %s, ignoring converter function..',
                self.__version['file'],
                input_range,
            )
            return

        try:
            self.__config = func(self.__config)
        except Exception as ex:
            log.exception(ex)
            log.error(
                'There was an exception try to convert config file %s %s to %s',
                self.__config_file,
                self.__version['file'],
                output_version,
            )
            raise ex
        else:
            self.__version['file'] = output_version
            self.save()

    @property
    def config_file(self):
        return self.__config_file

    @property
    def config(self):
        """The config dictionary"""
        return self.__config

    @config.deleter
    def config(self):
        return self.save()
