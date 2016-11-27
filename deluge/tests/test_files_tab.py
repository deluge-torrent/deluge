from __future__ import print_function

import pytest
from twisted.trial import unittest

import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.ui.translations_util import setup_translations

from . import common
from .basetest import BaseTestCase

libs_available = True
# Allow running other tests without GTKUI dependencies available
try:
    from deluge.ui.gtkui.mainwindow import MainWindow
    from deluge.ui.gtkui.gtkui import DEFAULT_PREFS
    from deluge.ui.gtkui.files_tab import FilesTab

except ImportError as err:
    libs_available = False
    import traceback
    traceback.print_exc()

setup_translations()


@pytest.mark.gtkui
class FilesTabTestCase(BaseTestCase):

    def set_up(self):
        if libs_available is False:
            raise unittest.SkipTest('GTKUI dependencies not available')

        common.set_tmp_config_dir()
        ConfigManager('gtkui.conf', defaults=DEFAULT_PREFS)
        self.mainwindow = MainWindow()
        self.filestab = FilesTab()
        self.t_id = '1'
        self.filestab.torrent_id = self.t_id
        self.index = 1

    def tear_down(self):
        return component.shutdown()

    def print_treestore(self, title, treestore):
        root = treestore.get_iter_root()
        level = 1

        def p_level(s, l):
            print('%s%s' % (' ' * l, s))

        def _print_treestore_children(i, lvl):
            while i:
                p_level(treestore[i][0], lvl)
                if treestore.iter_children(i):
                    _print_treestore_children(treestore.iter_children(i), lvl + 2)
                i = treestore.iter_next(i)

        print('\n%s' % title)
        _print_treestore_children(root, level)
        print('')

    def verify_treestore(self, treestore, tree):

        def _verify_treestore(itr, tree_values):
            i = 0
            while itr:
                values = tree_values[i]
                if treestore[itr][0] != values[0]:
                    return False
                if treestore.iter_children(itr):
                    if not _verify_treestore(treestore.iter_children(itr), values[1]):
                        return False
                itr = treestore.iter_next(itr)
                i += 1
            return True
        return _verify_treestore(treestore.get_iter_root(), tree)

    def test_files_tab(self):
        self.filestab.files_list[self.t_id] = ({u'index': 0, u'path': u'1/test_10.txt', u'offset': 0, u'size': 13},
                                               {u'index': 1, u'path': u'test_100.txt', u'offset': 13, u'size': 14})
        self.filestab.update_files()
        self.filestab._on_torrentfilerenamed_event(self.t_id, self.index, '2/test_100.txt')

        ret = self.verify_treestore(self.filestab.treestore, [['1/', [['test_10.txt']]], ['2/', [['test_100.txt']]]])
        if not ret:
            self.print_treestore('Treestore not expected:', self.filestab.treestore)
        self.assertTrue(ret)

    def test_files_tab2(self):
        self.filestab.files_list[self.t_id] = ({u'index': 0, u'path': u'1/1/test_10.txt', u'offset': 0, u'size': 13},
                                               {u'index': 1, u'path': u'test_100.txt', u'offset': 13, u'size': 14})
        self.filestab.update_files()
        self.filestab._on_torrentfilerenamed_event(self.t_id, self.index, '1/1/test_100.txt')

        ret = self.verify_treestore(self.filestab.treestore, [['1/', [['1/', [['test_100.txt'], ['test_10.txt']]]]]])
        if not ret:
            self.print_treestore('Treestore not expected:', self.filestab.treestore)
        self.assertTrue(ret)

    def test_files_tab3(self):
        self.filestab.files_list[self.t_id] = ({u'index': 0, u'path': u'1/test_10.txt', u'offset': 0, u'size': 13},
                                               {u'index': 1, u'path': u'test_100.txt', u'offset': 13, u'size': 14})
        self.filestab.update_files()
        self.filestab._on_torrentfilerenamed_event(self.t_id, self.index, '1/test_100.txt')

        ret = self.verify_treestore(self.filestab.treestore, [['1/', [['test_100.txt'], ['test_10.txt']]]])
        if not ret:
            self.print_treestore('Treestore not expected:', self.filestab.treestore)
        self.assertTrue(ret)

    def test_files_tab4(self):
        self.filestab.files_list[self.t_id] = ({u'index': 0, u'path': u'1/test_10.txt', u'offset': 0, u'size': 13},
                                               {u'index': 1, u'path': u'1/test_100.txt', u'offset': 13, u'size': 14})
        self.filestab.update_files()
        self.filestab._on_torrentfilerenamed_event(self.t_id, self.index, '1/2/test_100.txt')

        ret = self.verify_treestore(self.filestab.treestore, [['1/', [['2/', [['test_100.txt']]],
                                                                      ['test_10.txt']]]])
        if not ret:
            self.print_treestore('Treestore not expected:', self.filestab.treestore)
        self.assertTrue(ret)

    def test_files_tab5(self):
        self.filestab.files_list[self.t_id] = ({u'index': 0, u'path': u'1/test_10.txt', u'offset': 0, u'size': 13},
                                               {u'index': 1, u'path': u'2/test_100.txt', u'offset': 13, u'size': 14})
        self.filestab.update_files()
        self.filestab._on_torrentfilerenamed_event(self.t_id, self.index, '1/test_100.txt')

        ret = self.verify_treestore(self.filestab.treestore, [['1/', [['test_100.txt'], ['test_10.txt']]]])
        if not ret:
            self.print_treestore('Treestore not expected:', self.filestab.treestore)
        self.assertTrue(ret)
