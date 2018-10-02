# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os

import deluge.common
import deluge.log
from deluge.config import Config

log = logging.getLogger(__name__)


class _ConfigManager(object):
    def __init__(self):
        log.debug('ConfigManager started..')
        self.config_files = {}
        self.__config_directory = None

    @property
    def config_directory(self):
        if self.__config_directory is None:
            self.__config_directory = deluge.common.get_default_config_dir()
        return self.__config_directory

    def __del__(self):
        del self.config_files

    def set_config_dir(self, directory):
        """
        Sets the config directory.

        :param directory: str, the directory where the config info should be

        :returns bool: True if successfully changed directory, False if not
        """

        if not directory:
            return False

        # Ensure absolute dirpath
        directory = os.path.abspath(directory)

        log.info('Setting config directory to: %s', directory)
        if not os.path.exists(directory):
            # Try to create the config folder if it doesn't exist
            try:
                os.makedirs(directory)
            except OSError as ex:
                log.error('Unable to make config directory: %s', ex)
                return False
        elif not os.path.isdir(directory):
            log.error('Config directory needs to be a directory!')
            return False

        self.__config_directory = directory

        # Reset the config_files so we don't get config from old config folder
        # XXX: Probably should have it go through the config_files dict and try
        # to reload based on the new config directory
        self.save()
        self.config_files = {}
        deluge.log.tweak_logging_levels()

        return True

    def get_config_dir(self):
        return self.config_directory

    def close(self, config):
        """Closes a config file."""
        try:
            del self.config_files[config]
        except KeyError:
            pass

    def save(self):
        """Saves all the configs to disk."""
        for value in self.config_files.values():
            value.save()
        # We need to return True to keep the timer active
        return True

    def get_config(self, config_file, defaults=None, file_version=1):
        """Get a reference to the Config object for this filename"""
        log.debug('Getting config: %s', config_file)
        # Create the config object if not already created
        if config_file not in self.config_files:
            self.config_files[config_file] = Config(
                config_file,
                defaults,
                config_dir=self.config_directory,
                file_version=file_version,
            )

        return self.config_files[config_file]


# Singleton functions
_configmanager = _ConfigManager()


def ConfigManager(config, defaults=None, file_version=1):  # NOQA: N802
    return _configmanager.get_config(
        config, defaults=defaults, file_version=file_version
    )


def set_config_dir(directory):
    """Sets the config directory, else just uses default"""
    return _configmanager.set_config_dir(deluge.common.decode_bytes(directory))


def get_config_dir(filename=None):
    if filename is not None:
        return os.path.join(_configmanager.get_config_dir(), filename)
    else:
        return _configmanager.get_config_dir()


def close(config):
    return _configmanager.close(config)
