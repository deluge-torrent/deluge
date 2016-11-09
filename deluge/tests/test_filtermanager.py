import warnings

from mock import MagicMock

import deluge.component as component
from deluge.common import AUTH_LEVEL_NORMAL
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.core.torrent import Torrent
from deluge.filterdb import FilterDB

from . import common
from .basetest import BaseTestCase

warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.resetwarnings()


class FiltermanagerSQLiteTestCase(BaseTestCase):

    def create_test_torrent(self, torrent_id, owner='user', shared=True):
        m = MagicMock()
        m.info_hash = MagicMock(return_value=torrent_id)
        status = MagicMock()
        status.has_metadata = False
        m.status = MagicMock(return_value=status)
        t = Torrent(m, {'owner': owner, 'shared': shared})
        self.core.torrentmanager.torrents[torrent_id] = t
        return t

    def create_test_torrents(self, count=1, torrent_id=0, owner='user', shared=True):
        for c in range(count):
            t = self.create_test_torrent('%d' % torrent_id, owner=owner, shared=shared)
            torrent_id += 1
            yield t
        return

    def add_test_values(self, count, owner, torrent_id=0, shared=True):
        for t in self.create_test_torrents(count=count, torrent_id=torrent_id, owner=owner, shared=shared):
            self.fm.on_torrent_added(t.torrent_id, False)

    def set_up(self):
        common.set_tmp_config_dir()
        self.core = Core()
        self.fm = self.core.filtermanager
        self.rpcserver = RPCServer(listen=False)
        return component.start()

    def tear_down(self):
        self.core.torrentmanager.torrents.clear()
        return component.shutdown()

    def test_get_torrent_list(self):
        self.add_test_values(2, 'user1', torrent_id=0, shared=True)
        t_list = self.core.filtermanager.get_torrent_list()
        self.assertEquals(2, len(t_list))
        self.assertTrue('0' in t_list.keys())
        self.assertTrue('1' in t_list.keys())

    def test_get_torrent_list_nonshared(self):
        self.add_test_values(2, 'user1', torrent_id=0, shared=True)
        self.add_test_values(2, 'user2', torrent_id=2, shared=False)
        self.rpcserver.listen = True
        self.rpcserver.factory.session_id = 1
        self.rpcserver.factory.authorized_sessions[self.rpcserver.get_session_id()] = (AUTH_LEVEL_NORMAL, 'user1')
        torrent_ids = self.core.filtermanager.get_torrent_list()
        self.assertEquals(2, len(torrent_ids))

    def test_get_torrents_filter_admin(self):
        """The admin filter should empty, i.e. return all torrents"""
        f = self.core.filtermanager.get_torrents_filter()
        self.assertEquals(str(f), '')

    def test_get_torrents_filter(self):
        self.rpcserver.listen = True
        self.rpcserver.factory.session_id = 1
        self.rpcserver.factory.authorized_sessions[self.rpcserver.get_session_id()] = (AUTH_LEVEL_NORMAL, 'user1')
        f = self.core.filtermanager.get_torrents_filter()
        self.assertEquals(str(f), "((shared = 1) OR (owner = 'user1'))")


class FiltermanagerPyDbTestCase(FiltermanagerSQLiteTestCase):

    def set_up(self):
        d = super(FiltermanagerPyDbTestCase, self).set_up()
        self.core.filtermanager.filter_db = FilterDB(sqlite=False)
        return d
