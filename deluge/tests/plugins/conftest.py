# SPDX-License-Identifier: GPL-3.0-or-later WITH GPL-3.0-linking-exception

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

import deluge.common
from deluge.pluginmanagerbase import _extract_egg, _PluginDirFinder


@pytest.fixture(scope='session')
def builtin_egg_info_dir(tmp_path_factory):
    """Session-scoped: generate egg-info for all built-in plugins into a tmp dir.

    Runs ``setup.py egg_info --egg-base <tmp/plugins>`` for each built-in plugin
    so the plugin scanner can discover them without polluting the source tree.

    Returns the plugins/ Path containing all generated .egg-info directories.
    """
    plugins_dir = tmp_path_factory.mktemp('builtin_plugins')

    plugin_src_root = Path(deluge.common.resource_filename('deluge', 'plugins'))
    for plugin_dir in sorted(plugin_src_root.iterdir()):
        if not (plugin_dir / 'setup.py').is_file():
            continue

        subprocess.run(
            [sys.executable, 'setup.py', 'egg_info', '--egg-base', str(plugins_dir)],
            cwd=str(plugin_dir),
            check=True,
            capture_output=True,
        )
    return plugins_dir


@pytest.fixture()
def fake_egg(tmp_path):
    """Create a minimal bdist_egg zip in a plugins directory.

    Includes a Python module (fake_plugin) with a resource file (config.ui)
    and entry points, so it can be used for both discovery and resource tests.

    Returns:
        plugins_dir, egg_path
    """
    pkg_info = 'Metadata-Version: 1.0\nName: FakePlugin\nVersion: 0.1\n'
    ep_txt = '[deluge.plugin.core]\nFakePlugin = fake_plugin:CorePlugin\n'
    plugins_dir = tmp_path / 'plugins'
    plugins_dir.mkdir()
    egg_path = plugins_dir / 'FakePlugin-0.1-py3.egg'

    with zipfile.ZipFile(egg_path, 'w') as zf:
        zf.writestr('EGG-INFO/PKG-INFO', pkg_info)
        zf.writestr('EGG-INFO/entry_points.txt', ep_txt)
        zf.writestr('fake_plugin/__init__.py', '')
        zf.writestr('fake_plugin/config.ui', '<ui/>')
        zf.writestr('fake_plugin/data/script.js', 'console.log("test");')

    return plugins_dir, egg_path


@pytest.fixture()
def installed_fake_plugin(fake_egg, tmp_path):
    """Extract fake_egg and register it via _PluginDirFinder on sys.meta_path.

    Yields with fake_plugin importable via importlib.resources, then cleans up.
    """
    _, egg_path = fake_egg
    dest = tmp_path / 'extracted'
    _extract_egg(egg_path, dest)

    finder = _PluginDirFinder(dest)
    sys.meta_path.insert(0, finder)
    # Evict any cached module so the import goes through our finder
    sys.modules.pop('fake_plugin', None)
    yield
    sys.meta_path.remove(finder)
    sys.modules.pop('fake_plugin', None)
