#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


"""PluginManagerBase"""

import email
import importlib.metadata
import logging
import os.path
import sys
from typing import NamedTuple

import pkginfo
from twisted.internet import defer
from twisted.python.failure import Failure

import deluge.common
import deluge.component as component
import deluge.configmanager

log = logging.getLogger(__name__)

METADATA_KEYS = [
    'Name',
    'License',
    'Author',
    'Home-page',
    'Summary',
    'Platform',
    'Version',
    'Author-email',
    'Description',
]

DEPRECATION_WARNING = """
The plugin %s is not using the "deluge_" namespace.
In order to avoid package name clashes between regular python packages and
deluge plugins, the way deluge plugins should be created has changed.
If you're seeing this message and you're not the developer of the plugin which
triggered this warning, please report to it's author.
If you're the developer, please take a look at the plugins hosted on deluge's
git repository to have an idea of what needs to be changed.
"""


# This class exists largely to replicate
# the metadata provided by pkg_resources
class EggPlugin(NamedTuple):
    name: str
    version: str
    location: str
    author: str
    author_email: str
    homepage: str
    description: str


class PluginManagerBase:
    """PluginManagerBase is a base class for PluginManagers to inherit"""

    def __init__(self, config_file, entry_name):
        log.debug('Plugin manager init..')

        self.config = deluge.configmanager.ConfigManager(config_file)

        # Create the plugins folder if it doesn't exist
        if not os.path.exists(
            os.path.join(deluge.configmanager.get_config_dir(), 'plugins')
        ):
            os.mkdir(os.path.join(deluge.configmanager.get_config_dir(), 'plugins'))

        # This is the entry we want to load..
        self.entry_name = entry_name

        # Loaded plugins
        self.plugins = {}

        # Scan the plugin folders for plugins
        self.scan_for_plugins()

    def enable_plugins(self):
        # Load plugins that are enabled in the config.
        for name in self.config['enabled_plugins']:
            self.enable_plugin(name)

    def disable_plugins(self):
        """Disable all plugins that are enabled"""
        # Dict will be modified so iterate over generated list
        for key in list(self.plugins):
            self.disable_plugin(key)

    def __getitem__(self, key):
        return self.plugins[key]

    def get_available_plugins(self):
        """Returns a list of the available plugins name"""
        return [p.name for p in self.available_plugins]
        return self.available_plugins

    def get_enabled_plugins(self):
        """Returns a list of enabled plugins"""
        return list(self.plugins)

    def _get_egg_metadata(self, egg_path: str) -> EggPlugin:
        pkg_info = pkginfo.BDist(egg_path)
        if pkg_info.name is None or pkg_info.version is None:
            raise ValueError(
                f'Invalid .egg plugin {egg_path}: No name or version found'
            )
        return EggPlugin(
            name=pkg_info.name,
            version=pkg_info.version,
            location=egg_path,
            author=pkg_info.author or '',
            author_email=pkg_info.author_email or '',
            homepage=pkg_info.home_page or '',
            description=pkg_info.description or '',
        )

    def scan_for_plugins(self):
        """Scans for available plugins"""
        base_dir = deluge.common.resource_filename('deluge', 'plugins')
        user_dir = os.path.join(deluge.configmanager.get_config_dir(), 'plugins')
        base_subdir = [
            os.path.join(base_dir, f)
            for f in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, f))
        ]
        plugin_dirs = [base_dir, user_dir] + base_subdir

        self.available_plugins = []
        for dirname in plugin_dirs:
            for f in os.listdir(dirname):
                if f.endswith('.egg'):
                    full_path = os.path.join(dirname, f)
                    if full_path not in sys.path:
                        try:
                            self.available_plugins.append(
                                self._get_egg_metadata(full_path)
                            )
                            sys.path.insert(0, full_path)
                        except Exception as e:
                            log.warning(f'Failed to load .egg plugin {full_path}: {e}')

        for plugin in self.available_plugins:
            log.info(
                f'Found plugin: {plugin.name} {plugin.version} at {plugin.location}'
            )

    def enable_plugin(self, plugin_name):
        """Enable a plugin.

        Args:
            plugin_name (str): The plugin name.

        Returns:
            Deferred: A deferred with callback value True or False indicating
                whether the plugin is enabled or not.

        """
        if plugin_name not in [plugin.name for plugin in self.available_plugins]:
            log.warning('Cannot enable non-existent plugin %s', plugin_name)
            return defer.succeed(False)

        if plugin_name in self.plugins:
            log.warning('Cannot enable already enabled plugin %s', plugin_name)
            return defer.succeed(True)

        plugin_name = plugin_name.replace(' ', '-')
        log.debug(f'Enabling plugin: {plugin_name}')
        egg = None
        for plugin in self.available_plugins:
            if plugin.name == plugin_name:
                egg = plugin
                break
        if egg is None:
            raise ValueError(f'Could not find egg for plugin {plugin_name}')
        return_d = defer.succeed(True)
        entry_points = importlib.metadata.entry_points(name=egg.name)

        for ep in entry_points:
            try:
                cls = ep.load()
                instance = cls(plugin_name.replace('-', '_'))
            except component.ComponentAlreadyRegistered as ex:
                log.error(ex)
                return defer.succeed(False)
            except Exception as ex:
                log.error('Unable to instantiate plugin from %r!', egg.location)
                log.exception(ex)
                continue
            try:
                return_d = defer.maybeDeferred(instance.enable)
            except Exception as ex:
                log.error('Unable to enable plugin: %s', egg.location)
                log.exception(ex)
                return_d = defer.fail(False)

            if not instance.__module__.startswith('deluge_'):
                import warnings

                warnings.warn_explicit(
                    DEPRECATION_WARNING % ep.name,
                    DeprecationWarning,
                    instance.__module__,
                    0,
                )
            if self._component_state == 'Started':

                def on_enabled(result, instance):
                    return component.start([instance.plugin._component_name])

                return_d.addCallback(on_enabled, instance)

            def on_started(result, instance):
                plugin_name_space = plugin_name.replace('-', ' ')
                self.plugins[plugin_name_space] = instance
                if plugin_name_space not in self.config['enabled_plugins']:
                    log.debug(
                        'Adding %s to enabled_plugins list in config', plugin_name_space
                    )
                    self.config['enabled_plugins'].append(plugin_name_space)
                log.info('Plugin %s enabled...', plugin_name_space)
                return True

            def on_started_error(result, instance):
                log.error(
                    'Failed to start plugin: %s\n%s',
                    plugin_name,
                    result.getTraceback(elideFrameworkCode=1, detail='brief'),
                )
                self.plugins[plugin_name.replace('-', ' ')] = instance
                self.disable_plugin(plugin_name)
                return False

            return_d.addCallbacks(
                on_started,
                on_started_error,
                callbackArgs=[instance],
                errbackArgs=[instance],
            )
            return return_d

        return defer.succeed(False)

    def disable_plugin(self, name):
        """Disable a plugin.

        Args:
            plugin_name (str): The plugin name.

        Returns:
            Deferred: A deferred with callback value True or False indicating
                whether the plugin is disabled or not.

        """
        if name not in self.plugins:
            log.warning('Plugin "%s" is not enabled...', name)
            return defer.succeed(True)

        try:
            d = defer.maybeDeferred(self.plugins[name].disable)
        except Exception as ex:
            log.error('Error when disabling plugin: %s', self.plugin._component_name)
            log.debug(ex)
            d = defer.succeed(False)

        def on_disabled(result):
            ret = True
            if isinstance(result, Failure):
                log.debug(
                    'Error when disabling plugin %s: %s', name, result.getTraceback()
                )
                ret = False
            try:
                component.deregister(self.plugins[name].plugin)
                del self.plugins[name]
                self.config['enabled_plugins'].remove(name)
            except Exception as ex:
                log.warning('Problems occurred disabling plugin: %s', name)
                log.debug(ex)
                ret = False
            else:
                log.info('Plugin %s disabled...', name)
            return ret

        d.addBoth(on_disabled)
        return d

    def _get_plugin(self, name: str) -> EggPlugin | None:
        for plugin in self.available_plugins:
            if plugin.name == name:
                return plugin
        return None

    def get_plugin_info(self, name) -> dict[str, str]:
        """Returns a dictionary of plugin info from the metadata"""

        plugin = self._get_plugin(name)
        if not plugin:
            log.warning('Failed to retrieve info for plugin: %s', name)
            info = {}.fromkeys(METADATA_KEYS, '')
            info['Name'] = info['Version'] = 'not available'
            return info

        info: dict[str, str] = {
            'Author': plugin.author,
            'Version': plugin.version,
            'Author-email': plugin.author_email,
            'Home-page': plugin.homepage,
            'Description': plugin.description,
        }
        return info

    @staticmethod
    def parse_pkg_info(pkg_info) -> dict[str, str]:
        metadata_msg = email.message_from_string(pkg_info)
        metadata_ver = metadata_msg.get('Metadata-Version')

        info = {key: metadata_msg.get(key, '') for key in METADATA_KEYS}

        # Optional Description field in body (Metadata spec >=2.1)
        if not info['Description'] and metadata_ver.startswith('2'):
            info['Description'] = metadata_msg.get_payload().strip()

        return info
