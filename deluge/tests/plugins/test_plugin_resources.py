# SPDX-License-Identifier: GPL-3.0-or-later WITH GPL-3.0-linking-exception
from importlib import resources
from pathlib import Path

from deluge.pluginmanagerbase import _extract_egg


def test_extract_egg_creates_real_files(fake_egg, tmp_path):
    """Verify extraction produces real files on disk.

    Zip eggs serve resources from inside the archive, so non-Python assets
    (JS, UI files, etc.) must be extracted to disk to be accessible as real
    filesystem paths.
    """
    _, egg_path = fake_egg
    dest = tmp_path / 'extracted'
    _extract_egg(egg_path, dest)

    assert (dest / 'fake_plugin' / '__init__.py').exists()
    assert (dest / 'fake_plugin' / 'data' / 'script.js').exists()
    assert (
        dest / 'fake_plugin' / 'data' / 'script.js'
    ).read_text() == 'console.log("test");'


def test_extract_egg_skips_egg_info(fake_egg, tmp_path):
    """Test that EGG-INFO (setuptools package metadata) is excluded from extraction.

    Only importable code belongs in the cache dir, a top-level EGG-INFO directory
    could interfere with namespace package discovery by importlib.
    """
    _, egg_path = fake_egg
    dest = tmp_path / 'extracted'
    _extract_egg(egg_path, dest)

    assert not (dest / 'EGG-INFO').exists()


def test_plugin_dir_finder_resources_are_real_paths(installed_fake_plugin):
    """After activation via _PluginDirFinder, files() returns a real pathlib.Path."""
    resource = resources.files('fake_plugin') / 'data' / 'script.js'

    assert isinstance(resource, Path), f'Expected pathlib.Path, got {type(resource)}'
    assert resource.exists()
    assert resource.read_text() == 'console.log("test");'


def test_str_get_resource_gives_real_path(installed_fake_plugin):
    """Casting a resource path to str yields a real, resolvable filesystem path."""
    path_str = str(resources.files('fake_plugin') / 'data' / 'script.js')

    assert Path(path_str).exists(), f'Path does not exist: {path_str}'
