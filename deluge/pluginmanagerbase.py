#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


"""PluginManagerBase"""

import email
import importlib.abc
import importlib.machinery
import logging
import sys
import unicodedata
import zipfile
from functools import cached_property
from importlib.metadata import EntryPoints
from importlib.resources import files
from pathlib import Path

from twisted.internet import defer
from twisted.python.failure import Failure

import deluge.component as component
import deluge.configmanager
from deluge.common import VersionSplit

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


def _extract_egg(egg_path: Path, dest: Path) -> None:
    """Extract a .egg zip to dest, skipping EGG-INFO metadata."""
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(egg_path) as zf:
        for member in zf.namelist():
            if not member.startswith('EGG-INFO/'):
                zf.extract(member, dest)


def _read_egg_info(egg_info: 'Path | zipfile.Path') -> tuple[str, str]:
    """Read PKG-INFO and entry_points.txt from an egg-info directory.

    Accepts a filesystem Path or zipfile.Path pointing directly at the
    egg-info directory (e.g. EGG-INFO/ or PluginName.egg-info/).
    """
    pkg_info = (egg_info / 'PKG-INFO').read_text()
    ep_path = egg_info / 'entry_points.txt'
    ep_txt = ep_path.read_text() if ep_path.is_file() else ''
    return pkg_info, ep_txt


def _ep_module_root(entry_points: 'EntryPoints') -> str | None:
    """Return the top-level package name from the first entry point."""
    if ep := next(iter(entry_points), None):
        return ep.value.split(':')[0].split('.')[0]
    return None


def plugin_name_to_id(name: str) -> str:
    """Convert a plugin display name to its canonical id (lowercase kebab-case).

    Applies NFKD unicode normalization and ASCII encoding to handle non-ASCII names.
    Matches Python distribution name convention (PEP 503).
    """
    ascii_name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return ascii_name.lower().replace(' ', '-').replace('_', '-')


def _load_plugin_metadata(
    item_path: Path,
) -> tuple[Path, str, str] | None:
    """Detect plugin type and read (location, pkg_info, ep_txt), or None."""
    match item_path.suffix:
        case '.egg' if item_path.is_file():
            location = item_path
            pkg_info, ep_txt = _read_egg_info(zipfile.Path(location, 'EGG-INFO'))
        case '.egg' if item_path.is_dir():
            location = item_path
            pkg_info, ep_txt = _read_egg_info(location / 'EGG-INFO')
        case '.egg-info' if item_path.is_dir():
            location = item_path.parent
            pkg_info, ep_txt = _read_egg_info(item_path)
        case '.egg-link' if item_path.is_file():
            location = Path(item_path.read_text().splitlines()[0].strip())
            pkg_info, ep_txt = _read_egg_info(next(location.glob('*.egg-info')))
        case _:
            return None
    return location, pkg_info, ep_txt


def _parse_pkg_info(pkg_info: str) -> dict:
    """Parse a PKG-INFO string and return a dict of metadata fields."""
    metadata_msg = email.message_from_string(pkg_info)
    metadata_ver = metadata_msg.get('Metadata-Version')

    info = {key: metadata_msg.get(key, '') for key in METADATA_KEYS}

    # Optional Description field in body (Metadata spec >=2.1)
    if not info['Description'] and (metadata_ver or '').startswith('2'):
        info['Description'] = metadata_msg.get_payload().strip()

    return info


class _PluginDirFinder(importlib.abc.MetaPathFinder):
    """MetaPathFinder that loads top-level packages from a single directory.

    Used for both directory plugins and extracted zip egg plugins. Registered
    on sys.meta_path so it can be cleanly removed on plugin deactivation,
    without sys.path pollution or module cache issues.
    """

    def __init__(self, directory: Path):
        self._finder = importlib.machinery.FileFinder(
            str(directory),
            (importlib.machinery.SourceFileLoader, ['.py']),
            (importlib.machinery.SourcelessFileLoader, ['.pyc']),
        )

    def find_spec(self, fullname, _path, target=None):
        """Find a module spec for a top-level plugin package.

        Only handles top-level imports (e.g. deluge_foo), not namespace
        subpackage imports (e.g. deluge.plugins.foo).
        """
        if '.' in fullname:
            return None
        return self._finder.find_spec(fullname, target)

    def invalidate_caches(self):
        self._finder.invalidate_caches()


class _PluginDist:
    """Discovered plugin distribution.

    Attributes:
        name: Display name from PKG-INFO (e.g. "Foo Bar").
        id: Normalised distribution id (e.g. "foo-bar"), PEP 503.
        module_root: Top-level package from entry point (e.g. "deluge_foobar").
    """

    def __init__(
        self,
        name: str,
        version: str,
        location: Path,
        entry_points: EntryPoints,
        pkg_info: str,
    ):
        self.name = name
        self.id = plugin_name_to_id(name)
        self.version = version
        self.location = location
        self._entry_points = entry_points
        self._pkg_info = pkg_info
        self._finder: _PluginDirFinder | None = None
        self._active: bool = False
        self.module_root: str = _ep_module_root(entry_points) or self.id.replace(
            '-', '_'
        )

    @property
    def is_active(self) -> bool:
        """Returns True if the plugin is loaded and active, False if not."""
        return self._active

    @cached_property
    def info(self) -> dict:
        """Return a dict of plugin metadata fields."""
        return _parse_pkg_info(self._pkg_info)

    @property
    def entry_points(self) -> EntryPoints:
        """Return all the plugin's entry points."""
        return self._entry_points

    @cached_property
    def _egg_cache_dir(self) -> Path:
        cache_base = Path(deluge.configmanager.get_config_dir()) / 'plugin_cache'
        return cache_base / f'{self.id}-{self.version}'

    @classmethod
    def from_metadata(cls, location: Path, pkg_info: str, ep_txt: str) -> '_PluginDist':
        meta = email.message_from_string(pkg_info)
        entry_points = EntryPoints._from_text_for(ep_txt, None)
        return cls(
            name=meta.get('Name', ''),
            version=meta.get('Version', ''),
            location=location,
            entry_points=entry_points,
            pkg_info=pkg_info,
        )

    def activate(self):
        if self.is_active:
            return

        is_plugin_egg = self.location.is_file()

        if is_plugin_egg:
            plugin_dir = self._egg_cache_dir
            # Extract if new plugin egg or egg has changed
            if not plugin_dir.exists() or (
                self.location.stat().st_mtime_ns > plugin_dir.stat().st_mtime_ns
            ):
                _extract_egg(self.location, plugin_dir)
        else:
            plugin_dir = self.location

        self._finder = _PluginDirFinder(plugin_dir)
        sys.meta_path.insert(0, self._finder)
        self._active = True

    def deactivate(self):
        if self._finder:
            try:
                sys.meta_path.remove(self._finder)
            except ValueError:
                pass
            self._finder = None
        # Evict cached modules so a subsequent activate() re-imports cleanly.
        for key in list(sys.modules):
            if key == self.module_root or key.startswith(self.module_root + '.'):
                del sys.modules[key]
        self._active = False


class PluginManagerBase:
    """PluginManagerBase is a base class for PluginManagers to inherit"""

    def __init__(
        self,
        config_file: str,
        entry_name: str,
        plugin_dirs: list[str | Path] | None = None,
    ) -> None:
        """Initialise the plugin manager.

        Args:
            config_file: Name of the config file (e.g. 'core.conf').
            entry_name: The setuptools entry-point group to load plugins from
                (e.g. 'deluge.plugin.core').
            plugin_dirs: Directories to scan for plugins. Defaults to None,
                which uses the standard base and user plugin directories.
                Primarily intended for testing.
        """
        log.debug('Plugin manager init..')

        self.config = deluge.configmanager.ConfigManager(config_file)

        # Create the plugins folder if it doesn't exist
        (Path(deluge.configmanager.get_config_dir()) / 'plugins').mkdir(exist_ok=True)

        # This is the entry we want to load..
        self.entry_name = entry_name

        # Loaded plugins
        self.plugins = {}

        # Directories scanned for plugins
        self.plugin_dirs = plugin_dirs if plugin_dirs else self.default_plugin_dirs()

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
        return self.available_plugins

    def get_enabled_plugins(self):
        """Returns a list of enabled plugins"""
        return list(self.plugins)

    @staticmethod
    def default_plugin_dirs() -> list[Path]:
        """Returns the default directories to scan for plugins."""
        base_dir = Path(str(files('deluge') / 'plugins'))
        user_dir = Path(deluge.configmanager.get_config_dir()) / 'plugins'
        base_subdir = [item for item in base_dir.iterdir() if item.is_dir()]
        return [base_dir, user_dir] + base_subdir

    def scan_for_plugins(self) -> None:
        """Scan plugin_dirs for available plugins."""
        self._plugin_dist = {}
        self.available_plugins = []

        for scan_dir in self.plugin_dirs:
            scan_path = Path(scan_dir)
            if not scan_path.is_dir():
                continue
            for item in scan_path.iterdir():
                self.register_plugin(item)

    def register_plugin(self, plugin_path: Path) -> None:
        try:
            plugin_metadata = _load_plugin_metadata(plugin_path)
            plugin_dist = (
                _PluginDist.from_metadata(*plugin_metadata) if plugin_metadata else None
            )
        except Exception:
            log.warning(
                'Skipping %s: could not read plugin metadata',
                plugin_path,
                exc_info=True,
            )
            return

        if plugin_dist is None or not plugin_dist.name:
            return

        log.debug(
            'Found plugin: %s %s at %s',
            plugin_dist.name,
            plugin_dist.version,
            plugin_dist.location,
        )
        key = plugin_dist.id
        existing = self._plugin_dist.get(key)
        if existing:
            new_ver = VersionSplit(plugin_dist.version)
            old_ver = VersionSplit(existing.version)
            # Prefer newer version, or a source directory over a plugin of equal version.
            prefer_new = new_ver > old_ver or (
                new_ver == old_ver
                and existing.location.is_file()
                and plugin_dist.location.is_dir()
            )
            if not prefer_new:
                log.debug('Skipping duplicate plugin: %s at %s', key, plugin_path)
                return
            log.debug(
                'Replacing plugin %s %s at %s with %s at %s',
                key,
                existing.version,
                existing.location,
                plugin_dist.version,
                plugin_dist.location,
            )
            self.available_plugins.remove(existing.name)
        self._plugin_dist[key] = plugin_dist
        self.available_plugins.append(plugin_dist.name)

    def enable_plugin(self, plugin_name):
        """Enable a plugin.

        Args:
            plugin_name (str): The plugin name.

        Returns:
            Deferred: A deferred with callback value True or False indicating
                whether the plugin is enabled or not.

        """
        if plugin_name not in self.available_plugins:
            log.warning('Cannot enable non-existent plugin %s', plugin_name)
            return defer.succeed(False)

        if plugin_name in self.plugins:
            log.warning('Cannot enable already enabled plugin %s', plugin_name)
            return defer.succeed(True)

        plugin_key = plugin_name_to_id(plugin_name)
        plugin_dist = self._plugin_dist[plugin_key]
        plugin_dist.activate()
        return_d = defer.succeed(True)

        for ep in plugin_dist.entry_points.select(group=self.entry_name):
            try:
                cls = ep.load()
                instance = cls(plugin_dist.id)
            except component.ComponentAlreadyRegistered as ex:
                log.error(ex)
                return defer.succeed(False)
            except Exception as ex:
                log.error(
                    'Unable to instantiate plugin %r from %r!',
                    ep.name,
                    plugin_dist.location,
                )
                log.exception(ex)
                continue
            try:
                return_d = defer.maybeDeferred(instance.enable)
            except Exception as ex:
                log.error('Unable to enable plugin: %s', ep.name)
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
                display_name = plugin_dist.name
                self.plugins[display_name] = instance
                if display_name not in self.config['enabled_plugins']:
                    log.debug(
                        'Adding %s to enabled_plugins list in config', display_name
                    )
                    self.config['enabled_plugins'].append(display_name)
                log.info('Plugin %s enabled...', display_name)
                return True

            def on_started_error(result, instance):
                log.error(
                    'Failed to start plugin: %s\n%s',
                    plugin_dist.name,
                    result.getTraceback(elideFrameworkCode=1, detail='brief'),
                )
                self.plugins[plugin_dist.name] = instance
                self.disable_plugin(plugin_dist.name)
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
            log.error(
                'Error when disabling plugin: %s',
                self.plugins[name].plugin._component_name,
            )
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
                plugin_dist = self._plugin_dist.get(plugin_name_to_id(name))
                if plugin_dist:
                    plugin_dist.deactivate()
            except Exception as ex:
                log.warning('Problems occurred disabling plugin: %s', name)
                log.debug(ex)
                ret = False
            else:
                log.info('Plugin %s disabled...', name)
            return ret

        d.addBoth(on_disabled)
        return d

    def get_plugin_info(self, name):
        """Returns a dictionary of plugin info from the metadata"""
        plugin_dist = self._plugin_dist.get(plugin_name_to_id(name))
        if not plugin_dist:
            log.warning('Failed to retrieve info for plugin: %s', name)
            return {
                **dict.fromkeys(METADATA_KEYS, ''),
                'Name': 'not available',
                'Version': 'not available',
                'Location': '',
            }

        return {**plugin_dist.info, 'Location': str(plugin_dist.location)}
