import deluge.component as component
from deluge.ui.torrentfilter import TorrentFilter

from .basetest import BaseTestCase


class TorrentFilterTestCase(BaseTestCase):

    def set_up(self):
        self.tf = TorrentFilter()

    def tear_down(self):
        return component.shutdown()

    def test_add_torrent(self):
        torrent_id = 'id_abc'
        self.tf.add_torrent(torrent_id)
        self.assertTrue(torrent_id in self.tf.torrents)
        records = self.tf.filter_db(torrent_id=torrent_id)  # noqa pylint: disable=not-callable
        self.assertEquals(len(records), 1)

    def test_remove_torrent(self):
        torrent_id = 'id_abc'
        self.tf.add_torrent(torrent_id)
        self.tf.remove_torrent(torrent_id)
        self.assertFalse(torrent_id in self.tf.torrents)
        records = self.tf.filter_db(torrent_id=torrent_id)  # noqa pylint: disable=not-callable
        self.assertEquals(len(records), 0)

    def test_update_keys_bad_input_type(self):
        self.assertRaises(TypeError, self.tf.update_keys, 'string_input')

    def test_update_keys(self):
        self.tf.update_keys(['test_field'])
        self.assertTrue('test_field' in self.tf.filter_db.fields)

    def test_update_torrent(self):
        torrent_id = 'id_abc'
        self.tf.add_torrent(torrent_id)
        self.tf.update_torrent(torrent_id, {'key1': 'Value1'})
        self.assertTrue('key1' in self.tf.torrents[torrent_id])
        self.assertTrue(self.tf.torrents[torrent_id]['key1'], 'Value1')

    def test_filter_torrents_id(self):
        torrent_ids = ['id_a', 'id_b', 'id_c']
        for tid in torrent_ids:
            self.tf.add_torrent(tid)

        filter_d = {'id': [torrent_ids[0]]}
        f = self.tf.filter_torrents(filter_d)
        self.assertEquals(len(f), 1)
        for t in f:
            self.assertEquals(t['torrent_id'], u'id_a')

    def test_filter_torrents_state(self):
        torrent_ids = ['id_a', 'id_b', 'id_c']
        for tid in torrent_ids:
            self.tf.add_torrent(tid)
            self.tf.update_torrent(tid, {'download_payload_rate': 0})

        # Set this torrent active
        self.tf.update_torrent('id_a', {'download_payload_rate': 10})

        filter_d = {'state': 'Active'}
        f = self.tf.filter_torrents(filter_d)
        self.assertEquals(len(f), 1)
        for t in f:
            self.assertEquals(t['torrent_id'], u'id_a')

    def test_filter_torrents_search(self):
        torrent_ids = ['id_a', 'id_b', 'id_c']
        for tid in torrent_ids:
            self.tf.add_torrent(tid)
            self.tf.update_torrent(tid, {'name': tid})

        # Set this torrent active
        self.tf.update_torrent('id_a', {'download_payload_rate': 10})

        filter_d = {'search': {'expression': 'id_A', 'match_case': False}}
        f = self.tf.filter_torrents(filter_d)
        self.assertEquals(len(f), 1)
        for t in f:
            self.assertEquals(t['torrent_id'], u'id_a')

        # Test match case = True
        filter_d['search']['match_case'] = True
        f = self.tf.filter_torrents(filter_d)
        self.assertEquals(len(f), 0)

    def test_register_filter(self):
        def test_filter(torrents_filter, values):
            for v in values:
                torrents_filter |= (torrents_filter.db('owner') == v)  # noqa
            return torrents_filter

        self.tf.register_filter('test_filter', test_filter)
        self.assertTrue('test_filter' in self.tf.registered_filters)
        self.assertEquals(self.tf.registered_filters['test_filter'], test_filter)

    def test_deregister_filter(self):
        self.tf.register_filter('test_filter', None)
        self.tf.deregister_filter('test_filter')
        self.assertFalse('test_filter' in self.tf.registered_filters)

    def test_register_filter_field(self):
        self.tf.register_filter_field('test_field', 'TEXT')
        self.assertTrue('test_field' in self.tf.filter_db.fields)
