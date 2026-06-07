# SPDX-License-Identifier: GPL-3.0-or-later WITH GPL-3.0-linking-exception

"""Tests for the Label plugin core."""

import sys
from pathlib import Path
from unittest import mock

import pytest

import deluge.common


@pytest.fixture
def label_core_module():
    """Import the Label plugin core module from the plugin source tree."""
    label_dir = Path(deluge.common.resource_filename('deluge', 'plugins')) / 'Label'
    sys.path.insert(0, str(label_dir))
    try:
        from deluge_label import core

        yield core
    finally:
        sys.path.remove(str(label_dir))


@pytest.fixture
def label_core(label_core_module):
    """A Label plugin Core with mocked config and no component framework."""
    plugin_core = label_core_module.Core.__new__(label_core_module.Core)
    plugin_core.labels = {}
    plugin_core.torrent_labels = {}
    plugin_core.torrents = {}
    plugin_core.config = mock.MagicMock()
    plugin_core.core_cfg = mock.MagicMock()
    return plugin_core


def make_label(label_core_module, **options):
    label_options = dict(label_core_module.OPTIONS_DEFAULTS)
    label_options.update(options)
    return label_options


def make_torrent(is_finished, download_location='/downloads'):
    torrent = mock.MagicMock()
    torrent.is_finished = is_finished
    torrent.options = {'download_location': download_location}
    return torrent


MOVE_OPTIONS = {
    'apply_move_completed': True,
    'move_completed': True,
    'move_completed_path': '/downloads/movies',
}


def test_set_torrent_moves_already_finished_torrent(label_core_module, label_core):
    """Applying a label after completion moves the data to the label path."""
    label_core.labels['movies'] = make_label(label_core_module, **MOVE_OPTIONS)
    torrent = make_torrent(is_finished=True)
    label_core.torrents['t1'] = torrent

    label_core.set_torrent('t1', 'movies')

    torrent.move_storage.assert_called_once_with('/downloads/movies')


def test_set_torrent_does_not_move_unfinished_torrent(label_core_module, label_core):
    """An unfinished torrent is moved at completion by core, not by the plugin."""
    label_core.labels['movies'] = make_label(label_core_module, **MOVE_OPTIONS)
    torrent = make_torrent(is_finished=False)
    label_core.torrents['t1'] = torrent

    label_core.set_torrent('t1', 'movies')

    torrent.move_storage.assert_not_called()


def test_set_torrent_does_not_move_torrent_already_at_path(
    label_core_module, label_core
):
    """No move when the torrent already lives at the label's move path."""
    label_core.labels['movies'] = make_label(label_core_module, **MOVE_OPTIONS)
    torrent = make_torrent(is_finished=True, download_location='/downloads/movies')
    label_core.torrents['t1'] = torrent

    label_core.set_torrent('t1', 'movies')

    torrent.move_storage.assert_not_called()


def test_set_torrent_does_not_move_without_move_completed(
    label_core_module, label_core
):
    """No move when the label does not enable move_completed."""
    label_core.labels['movies'] = make_label(
        label_core_module,
        apply_move_completed=True,
        move_completed=False,
        move_completed_path='/downloads/movies',
    )
    torrent = make_torrent(is_finished=True)
    label_core.torrents['t1'] = torrent

    label_core.set_torrent('t1', 'movies')

    torrent.move_storage.assert_not_called()


def test_set_torrent_does_not_move_with_empty_path(label_core_module, label_core):
    """No move when the label's move path is empty."""
    label_core.labels['movies'] = make_label(
        label_core_module,
        apply_move_completed=True,
        move_completed=True,
        move_completed_path='',
    )
    torrent = make_torrent(is_finished=True)
    label_core.torrents['t1'] = torrent

    label_core.set_torrent('t1', 'movies')

    torrent.move_storage.assert_not_called()


def test_set_options_moves_already_finished_labeled_torrents(
    label_core_module, label_core
):
    """Updating label options re-applies them, moving finished labeled torrents."""
    label_core.labels['movies'] = make_label(label_core_module)
    torrent = make_torrent(is_finished=True)
    label_core.torrents['t1'] = torrent
    label_core.torrent_labels['t1'] = 'movies'

    label_core.set_options('movies', dict(MOVE_OPTIONS))

    torrent.move_storage.assert_called_once_with('/downloads/movies')
