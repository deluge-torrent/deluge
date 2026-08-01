# SPDX-License-Identifier: GPL-3.0-or-later WITH GPL-3.0-linking-exception

import pytest

from deluge.plugins.Label.deluge_label import core as label_core

CORE_DEFAULTS = {
    'max_download_speed_per_torrent': -1,
    'max_upload_speed_per_torrent': -1,
    'max_connections_per_torrent': -1,
    'max_upload_slots_per_torrent': -1,
    'prioritize_first_last_pieces': False,
    'auto_managed': True,
    'stop_seed_at_ratio': False,
    'stop_seed_ratio': 2.0,
    'remove_seed_at_ratio': False,
    'move_completed': False,
    'move_completed_path': '',
}


class FakeConfig:
    def __init__(self):
        self.saved = False

    def save(self):
        self.saved = True


class FakeTorrent:
    def __init__(self, torrent_id, trackers=None):
        self.torrent_id = torrent_id
        self.trackers = trackers or []
        self.calls = []

    def _record(self, name, value):
        self.calls.append((name, value))

    def set_max_download_speed(self, value):
        self._record('set_max_download_speed', value)

    def set_max_upload_speed(self, value):
        self._record('set_max_upload_speed', value)

    def set_max_connections(self, value):
        self._record('set_max_connections', value)

    def set_max_upload_slots(self, value):
        self._record('set_max_upload_slots', value)

    def set_prioritize_first_last_pieces(self, value):
        self._record('set_prioritize_first_last_pieces', value)

    def set_auto_managed(self, value):
        self._record('set_auto_managed', value)

    def set_stop_at_ratio(self, value):
        self._record('set_stop_at_ratio', value)

    def set_stop_ratio(self, value):
        self._record('set_stop_ratio', value)

    def set_remove_at_ratio(self, value):
        self._record('set_remove_at_ratio', value)

    def set_options(self, value):
        self._record('set_options', value)


def build_core(torrents, labels, torrent_labels=None):
    core = object.__new__(label_core.Core)
    core.torrents = torrents
    core.labels = labels
    core.torrent_labels = torrent_labels if torrent_labels is not None else {}
    core.config = FakeConfig()
    core.core_cfg = FakeConfig()
    core.core_cfg.config = dict(CORE_DEFAULTS)
    return core


def make_labels(*ids):
    return {label: dict(label_core.OPTIONS_DEFAULTS) for label in ids}


def test_clean_initial_config_migrates_single_label():
    core = build_core(
        {}, make_labels('a', 'b'), {'t1': 'a', 't2': None, 't3': ['a', 'b']}
    )
    core.clean_initial_config()
    assert core.torrent_labels == {'t1': ['a'], 't2': [], 't3': ['a', 'b']}


def test_clean_initial_config_adds_priority_default():
    labels = {'a': {'apply_max': True, 'max_download_speed': 10}}
    core = build_core({}, labels)
    core.clean_initial_config()
    assert core.labels['a']['priority'] == 0
    assert core.labels['a']['apply_max'] is True


def test_normalize_labels_accepts_str_and_list():
    core = build_core({}, make_labels('x', 't'))
    assert core._normalize_labels('x') == ['x']
    assert core._normalize_labels(['x', 't']) == ['x', 't']
    assert core._normalize_labels(None) == []
    assert core._normalize_labels('') == []
    assert core._normalize_labels(label_core.NO_LABEL) == []


def test_normalize_labels_rejects_unknown():
    core = build_core({}, make_labels('x'))
    with pytest.raises(Exception):
        core._normalize_labels('unknown')
    with pytest.raises(Exception):
        core._normalize_labels(['x', 'unknown'])


def test_set_torrent_accepts_str_and_list():
    torrents = {'t1': FakeTorrent('t1')}
    core = build_core(torrents, make_labels('x', 't'))
    core.set_torrent('t1', 'x')
    assert core.torrent_labels == {'t1': ['x']}
    core.set_torrent('t1', ['x', 't'])
    assert core.torrent_labels == {'t1': ['x', 't']}
    core.set_torrent('t1', '')
    assert core.torrent_labels == {}
    assert core.config.saved


def test_add_label_dedupes():
    torrents = {'t1': FakeTorrent('t1')}
    core = build_core(torrents, make_labels('x', 't'))
    core.add_label('t1', 'x')
    core.add_label('t1', ['t', 'x'])
    assert core.torrent_labels == {'t1': ['x', 't']}


def test_remove_label():
    torrents = {'t1': FakeTorrent('t1')}
    core = build_core(torrents, make_labels('x', 't'), {'t1': ['x', 't']})
    core.remove_label('t1', 'x')
    assert core.torrent_labels == {'t1': ['t']}
    core.remove_label('t1', 't')
    assert core.torrent_labels == {}


def test_get_torrent_labels():
    core = build_core({}, make_labels('x', 't'), {'t1': ['x', 't'], 't2': []})
    assert core.get_torrent_labels('t1') == ['x', 't']
    assert core.get_torrent_labels('t2') == []
    assert core.get_torrent_labels('missing') == []


def test_status_get_label_returns_list():
    core = build_core({}, make_labels('x', 't'), {'t1': ['x', 't']})
    assert core._status_get_label('t1') == ['x', 't']
    assert core._status_get_label('missing') == []


def test_filter_label_matches_any():
    core = build_core(
        {}, make_labels('x', 't'), {'t1': ['x', 't'], 't2': ['x'], 't3': []}
    )
    assert list(core._filter_label(['t1', 't2', 't3'], ['t'])) == ['t1']
    assert list(core._filter_label(['t1', 't2', 't3'], ['x'])) == ['t1', 't2']
    assert list(core._filter_label(['t1', 't2', 't3'], [label_core.NO_LABEL])) == ['t3']
    assert list(core._filter_label(['t1', 't2', 't3'], [''])) == ['t3']


def test_clean_config_removes_invalid():
    torrents = {'t1': FakeTorrent('t1'), 't2': FakeTorrent('t2')}
    core = build_core(
        torrents, make_labels('x'), {'t1': ['x', 'gone'], 't3': ['x'], 't2': []}
    )
    core.clean_config()
    assert core.torrent_labels == {'t1': ['x']}


def test_reapply_options_priority_wins():
    labels = {
        'low': dict(
            label_core.OPTIONS_DEFAULTS,
            apply_max=True,
            max_download_speed=100,
            priority=0,
        ),
        'high': dict(
            label_core.OPTIONS_DEFAULTS,
            apply_max=True,
            max_download_speed=500,
            priority=10,
        ),
    }
    torrent = FakeTorrent('t1')
    core = build_core({'t1': torrent}, labels, {'t1': ['low', 'high']})

    core._reapply_torrent_options('t1')

    speeds = [v for name, v in torrent.calls if name == 'set_max_download_speed']
    # reset to core default, then low (100), then high (500) wins
    assert speeds == [-1, 100, 500]


def test_reapply_options_only_manages_applied_groups():
    labels = {
        'speed': dict(
            label_core.OPTIONS_DEFAULTS, apply_max=True, max_download_speed=100
        ),
        'folder': dict(
            label_core.OPTIONS_DEFAULTS,
            apply_move_completed=True,
            move_completed=True,
            move_completed_path='/dest',
        ),
    }
    torrent = FakeTorrent('t1')
    core = build_core({'t1': torrent}, labels, {'t1': ['speed', 'folder']})

    core._reapply_torrent_options('t1')

    names = [name for name, _ in torrent.calls]
    assert 'set_max_download_speed' in names
    assert 'set_options' in names
    assert 'set_auto_managed' not in names
