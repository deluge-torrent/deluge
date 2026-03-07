# SPDX-License-Identifier: GPL-3.0-or-later WITH GPL-3.0-linking-exception
import sys
import zipfile
from importlib.metadata import EntryPoints
from pathlib import Path

import pytest

from deluge.pluginmanagerbase import (
    PluginManagerBase,
    _load_plugin_metadata,
    _parse_pkg_info,
    _PluginDist,
    plugin_name_to_id,
)


def test_parse_pkg_info_metadata_1_x_no_description():
    """Metadata 1.x has no body fallback; Description must be empty string."""
    pkg_info = 'Metadata-Version: 1.0\nName: Foo\nVersion: 0.1\n'
    info = _parse_pkg_info(pkg_info)
    assert info['Description'] == ''


def test_parse_pkg_info_metadata_2_1():
    pkg_info = """Metadata-Version: 2.1
Name: AutoAdd
Version: 1.8
Summary: Monitors folders for .torrent files.
Home-page: http://dev.deluge-torrent.org/wiki/Plugins/AutoAdd
Author: Chase Sterling, Pedro Algarvio
Author-email: chase.sterling@gmail.com, pedro@algarvio.me
License: GPLv3
Platform: UNKNOWN

Monitors folders for .torrent files.
    """
    plugin_info = _parse_pkg_info(pkg_info)
    for value in plugin_info.values():
        assert value != ''
    result = 'Monitors folders for .torrent files.'
    assert plugin_info['Description'] == result


def test_scan_finds_specific_builtin_plugins(builtin_egg_info_dir):
    """Well-known built-in plugins must all be present."""
    expected = [
        'AutoAdd',
        'Blocklist',
        'Execute',
        'Extractor',
        'Label',
        'Notifications',
        'Scheduler',
        'Stats',
        'Toggle',
        'WebUi',
    ]
    pm = PluginManagerBase(
        'core.conf', 'deluge.plugin.core', plugin_dirs=[builtin_egg_info_dir]
    )
    assert sorted(pm.available_plugins) == expected


def test_plugin_info_all_values_are_strings(builtin_egg_info_dir):
    """All values from get_plugin_info must be strings, with Name and Version always set."""
    pm = PluginManagerBase(
        'core.conf', 'deluge.plugin.core', plugin_dirs=[builtin_egg_info_dir]
    )
    for plugin in pm.available_plugins:
        info = pm.get_plugin_info(plugin)
        for key, value in info.items():
            assert isinstance(key, str), f'{plugin}: key {key!r} is not str'
            assert isinstance(value, str), f'{plugin}: value for {key!r} is not str'
        assert info['Name'], f'{plugin}: Name is empty'
        assert info['Version'], f'{plugin}: Version is empty'


def test_plugin_info_invalid_name():
    """get_plugin_info for unknown plugin returns sentinel values."""
    pm = PluginManagerBase('core.conf', 'deluge.plugin.core', plugin_dirs=[])
    info = pm.get_plugin_info('NonExistentPlugin')
    assert info['Name'] == 'not available'
    assert info['Version'] == 'not available'


def test_scan_egg_zip(fake_egg):
    """A minimal .egg zip dropped in the plugins dir must be discovered."""
    plugins_dir, _ = fake_egg
    pm = PluginManagerBase('core.conf', 'deluge.plugin.core', plugin_dirs=[plugins_dir])
    assert 'FakePlugin' in pm.available_plugins


def test_scan_egg_link(tmp_path):
    """A .egg-link file pointing at a source dir must be discovered."""
    source_dir = tmp_path / 'MyPlugin'
    egg_info_dir = source_dir / 'MyPlugin.egg-info'
    egg_info_dir.mkdir(parents=True)
    (egg_info_dir / 'PKG-INFO').write_text(
        'Metadata-Version: 1.0\nName: MyPlugin\nVersion: 0.1\n'
    )
    (egg_info_dir / 'entry_points.txt').write_text(
        '[deluge.plugin.core]\nMyPlugin = my_plugin:CorePlugin\n'
    )

    plugins_dir = tmp_path / 'plugins'
    plugins_dir.mkdir()
    (plugins_dir / 'MyPlugin.egg-link').write_text(str(source_dir) + '\n.\n')

    pm = PluginManagerBase('core.conf', 'deluge.plugin.core', plugin_dirs=[plugins_dir])
    assert 'MyPlugin' in pm.available_plugins
    assert pm.get_plugin_info('MyPlugin')['Version'] == '0.1'
    assert pm._plugin_dist['myplugin'].entry_points.select(group='deluge.plugin.core')


def test_scan_unpacked_egg_dir(tmp_path):
    """An unpacked .egg directory (Ubuntu-style) with EGG-INFO/ must be discovered."""
    plugins_dir = tmp_path / 'plugins'
    plugins_dir.mkdir()
    egg_dir = plugins_dir / 'FakePlugin-0.1-py3.egg'
    egg_info = egg_dir / 'EGG-INFO'
    egg_info.mkdir(parents=True)
    (egg_info / 'PKG-INFO').write_text(
        'Metadata-Version: 1.0\nName: FakePlugin\nVersion: 0.1\n'
    )
    (egg_info / 'entry_points.txt').write_text(
        '[deluge.plugin.core]\nFakePlugin = fake_plugin:CorePlugin\n'
    )

    pm = PluginManagerBase('core.conf', 'deluge.plugin.core', plugin_dirs=[plugins_dir])
    assert 'FakePlugin' in pm.available_plugins
    assert pm.get_plugin_info('FakePlugin')['Version'] == '0.1'


def test_scan_egg_zip_plugin_info(fake_egg):
    """get_plugin_info returns correct metadata read from EGG-INFO/PKG-INFO inside a zip egg."""
    plugins_dir, _ = fake_egg
    pm = PluginManagerBase('core.conf', 'deluge.plugin.core', plugin_dirs=[plugins_dir])
    info = pm.get_plugin_info('FakePlugin')
    assert info['Name'] == 'FakePlugin'
    assert info['Version'] == '0.1'


def test_no_duplicate_plugins(fake_egg):
    """The same plugin discovered in multiple scan dirs must appear only once."""
    plugins_dir, _ = fake_egg
    # Pass the same dir twice to simulate the plugin appearing in multiple scan paths
    pm = PluginManagerBase(
        'core.conf', 'deluge.plugin.core', plugin_dirs=[plugins_dir, plugins_dir]
    )
    names = [n for n in pm.available_plugins if n == 'FakePlugin']
    assert len(names) == 1


def test_higher_version_wins(tmp_path):
    """When two eggs for the same plugin are found, the higher version must be kept."""

    def make_egg(directory, version):
        pkg_info = f'Metadata-Version: 1.0\nName: FakePlugin\nVersion: {version}\n'
        egg_path = directory / f'FakePlugin-{version}-py3.egg'
        with zipfile.ZipFile(egg_path, 'w') as zf:
            zf.writestr('EGG-INFO/PKG-INFO', pkg_info)
            zf.writestr('EGG-INFO/entry_points.txt', '')
        return egg_path

    old_dir = tmp_path / 'old'
    new_dir = tmp_path / 'new'
    old_dir.mkdir()
    new_dir.mkdir()
    make_egg(old_dir, '0.1')
    make_egg(new_dir, '0.2')

    pm = PluginManagerBase(
        'core.conf', 'deluge.plugin.core', plugin_dirs=[old_dir, new_dir]
    )
    assert pm.get_plugin_info('FakePlugin')['Version'] == '0.2'


@pytest.mark.parametrize(
    'name, expected',
    [
        ('AutoAdd', 'autoadd'),
        ('Auto Add', 'auto-add'),
        ('my-plugin', 'my-plugin'),
        ('my_plugin', 'my-plugin'),
        ('My Plugin', 'my-plugin'),
        ('Caf\u00e9', 'cafe'),  # NFKD strips combining accent
    ],
)
def test_plugin_name_to_id(name, expected):
    """plugin_name_to_id must return lowercase kebab-case ASCII."""
    assert plugin_name_to_id(name) == expected


def test_plugin_info_has_location(fake_egg):
    """get_plugin_info must include a non-empty Location string."""
    plugins_dir, _ = fake_egg
    pm = PluginManagerBase('core.conf', 'deluge.plugin.core', plugin_dirs=[plugins_dir])
    info = pm.get_plugin_info('FakePlugin')
    assert 'Location' in info
    assert info['Location']  # non-empty
    assert Path(info['Location']).exists()


def test_load_plugin_metadata_ignores_unknown_files(tmp_path):
    """_load_plugin_metadata must return None for files it doesn't recognise."""
    junk = tmp_path / 'something.txt'
    junk.write_text('irrelevant')
    assert _load_plugin_metadata(junk) is None


def test_deactivate_clears_module_cache(tmp_path):
    """deactivate() must evict the plugin package and its submodules from sys.modules."""
    dist = _PluginDist(
        name='FakePlugin',
        version='0.1',
        location=tmp_path,
        entry_points=EntryPoints(),
        pkg_info='',
    )
    dist._active = True

    # Simulate modules loaded when the plugin was active
    sys.modules['fakeplugin'] = object()
    sys.modules['fakeplugin.core'] = object()

    dist.deactivate()

    assert 'fakeplugin' not in sys.modules
    assert 'fakeplugin.core' not in sys.modules


def test_deactivate_evicts_entry_point_module(tmp_path):
    """deactivate() must use the entry point module name, not the dist id.

    For deluge plugins the top-level package (e.g. deluge_fakeplugin) differs
    from the distribution id (e.g. fakeplugin). The eviction must target the
    actual imported package, derived from the entry point value.
    """
    ep_txt = '[deluge.plugin.core]\nFakePlugin = deluge_fakeplugin:CorePlugin\n'
    eps = EntryPoints._from_text_for(ep_txt, None)
    dist = _PluginDist(
        name='FakePlugin',
        version='0.1',
        location=tmp_path,
        entry_points=eps,
        pkg_info='',
    )
    dist._active = True

    sys.modules['deluge_fakeplugin'] = object()
    sys.modules['deluge_fakeplugin.core'] = object()

    dist.deactivate()

    assert 'deluge_fakeplugin' not in sys.modules
    assert 'deluge_fakeplugin.core' not in sys.modules
