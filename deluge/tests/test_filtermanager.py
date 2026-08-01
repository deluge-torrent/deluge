# SPDX-License-Identifier: GPL-3.0-or-later WITH GPL-3.0-linking-exception

from deluge.core.filtermanager import FilterManager


class FakeTorrents:
    def __init__(self, torrent_ids):
        self._ids = list(torrent_ids)
        self.torrents = {tid: object() for tid in self._ids}

    def get_torrent_list(self):
        return list(self._ids)

    def separate_keys(self, keys, torrent_ids):
        return [], list(keys)


class FakeCore:
    def __init__(self, status_map):
        self.status_map = status_map

    def create_torrent_status(self, torrent_id, torrent_keys, plugin_keys):
        return {key: self.status_map[torrent_id][key] for key in plugin_keys}


def make_filter_manager(status_map, tree_fields):
    fm = object.__new__(FilterManager)
    fm.torrents = FakeTorrents(list(status_map))
    fm.core = FakeCore(status_map)
    fm.tree_fields = tree_fields
    fm.registered_filters = {}
    return fm


STATUS = {
    "t1": {"label": ["a", "b"]},
    "t2": {"label": ["a"]},
    "t3": {"label": []},
}


def test_get_filter_tree_counts_list_values():
    fm = make_filter_manager(STATUS, {"label": lambda: {}})
    counts = dict(fm.get_filter_tree()["label"])
    assert counts["a"] == 2
    assert counts["b"] == 1
    assert counts[""] == 1


def test_get_filter_tree_counts_scalar_values():
    status = {"t1": {"state": "Downloading"}, "t2": {"state": "Seeding"}}
    fm = make_filter_manager(status, {"state": lambda: {"All": 2}})
    counts = dict(fm.get_filter_tree()["state"])
    assert counts["All"] == 2
    assert counts["Downloading"] == 1
    assert counts["Seeding"] == 1


def test_filter_torrent_ids_matches_list_value():
    fm = make_filter_manager(STATUS, {})
    assert fm.filter_torrent_ids({"label": ["b"]}) == ["t1"]
    assert sorted(fm.filter_torrent_ids({"label": ["a"]})) == ["t1", "t2"]


def test_filter_torrent_ids_scalar_value_still_works():
    status = {"t1": {"state": "Downloading"}, "t2": {"state": "Seeding"}}
    fm = make_filter_manager(status, {})
    assert fm.filter_torrent_ids({"state": "Downloading"}) == ["t1"]


def test_filter_torrent_ids_empty_list_matches_no_label():
    fm = make_filter_manager(STATUS, {})
    assert fm.filter_torrent_ids({"label": [""]}) == ["t3"]
