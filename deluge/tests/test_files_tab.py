# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function, unicode_literals

import pytest
from twisted.trial import unittest

import deluge.component as component
from deluge.common import windows_check
from deluge.configmanager import ConfigManager
from deluge.i18n import setup_translation

from . import common
from .basetest import BaseTestCase

libs_available = True
# Allow running other tests without GTKUI dependencies available
try:
    from deluge.ui.gtk3.files_tab import FilesTab
    from deluge.ui.gtk3.gtkui import DEFAULT_PREFS
    from deluge.ui.gtk3.mainwindow import MainWindow
except (ImportError, ValueError):
    # gi.require_version gives ValueError if library not available
    libs_available = False

setup_translation()


@pytest.mark.gtkui
class FilesTabTestCase(BaseTestCase):
    def set_up(self):
        if libs_available is False:
            raise unittest.SkipTest('GTKUI dependencies not available')

        common.set_tmp_config_dir()
        ConfigManager('gtk3ui.conf', defaults=DEFAULT_PREFS)
        self.mainwindow = MainWindow()
        self.filestab = FilesTab()
        self.t_id = '1'
        self.filestab.torrent_id = self.t_id
        self.index = 1

    def tear_down(self):
        return component.shutdown()

    def print_treestore(self, title, treestore):
        root = treestore.get_iter_first()
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

        return _verify_treestore(treestore.get_iter_first(), tree)

    def test_files_tab(self):
        self.filestab.files_list[self.t_id] = (
            {'index': 0, 'path': '1/test_10.txt', 'offset': 0, 'size': 13},
            {'index': 1, 'path': 'test_100.txt', 'offset': 13, 'size': 14},
        )
        self.filestab.update_files()
        self.filestab._on_torrentfilerenamed_event(
            self.t_id, self.index, '2/test_100.txt'
        )

        ret = self.verify_treestore(
            self.filestab.treestore,
            [['1/', [['test_10.txt']]], ['2/', [['test_100.txt']]]],
        )
        if not ret:
            self.print_treestore('Treestore not expected:', self.filestab.treestore)
        self.assertTrue(ret)

    def test_files_tab2(self):
        if windows_check():
            raise unittest.SkipTest('on windows \\ != / for path names')
        self.filestab.files_list[self.t_id] = (
            {'index': 0, 'path': '1/1/test_10.txt', 'offset': 0, 'size': 13},
            {'index': 1, 'path': 'test_100.txt', 'offset': 13, 'size': 14},
        )
        self.filestab.update_files()
        self.filestab._on_torrentfilerenamed_event(
            self.t_id, self.index, '1/1/test_100.txt'
        )

        ret = self.verify_treestore(
            self.filestab.treestore,
            [['1/', [['1/', [['test_100.txt'], ['test_10.txt']]]]]],
        )
        if not ret:
            self.print_treestore('Treestore not expected:', self.filestab.treestore)
        self.assertTrue(ret)

    def test_files_tab3(self):
        if windows_check():
            raise unittest.SkipTest('on windows \\ != / for path names')
        self.filestab.files_list[self.t_id] = (
            {'index': 0, 'path': '1/test_10.txt', 'offset': 0, 'size': 13},
            {'index': 1, 'path': 'test_100.txt', 'offset': 13, 'size': 14},
        )
        self.filestab.update_files()
        self.filestab._on_torrentfilerenamed_event(
            self.t_id, self.index, '1/test_100.txt'
        )

        ret = self.verify_treestore(
            self.filestab.treestore, [['1/', [['test_100.txt'], ['test_10.txt']]]]
        )
        if not ret:
            self.print_treestore('Treestore not expected:', self.filestab.treestore)
        self.assertTrue(ret)

    def test_files_tab4(self):
        self.filestab.files_list[self.t_id] = (
            {'index': 0, 'path': '1/test_10.txt', 'offset': 0, 'size': 13},
            {'index': 1, 'path': '1/test_100.txt', 'offset': 13, 'size': 14},
        )
        self.filestab.update_files()
        self.filestab._on_torrentfilerenamed_event(
            self.t_id, self.index, '1/2/test_100.txt'
        )

        ret = self.verify_treestore(
            self.filestab.treestore,
            [['1/', [['2/', [['test_100.txt']]], ['test_10.txt']]]],
        )
        if not ret:
            self.print_treestore('Treestore not expected:', self.filestab.treestore)
        self.assertTrue(ret)

    def test_files_tab5(self):
        if windows_check():
            raise unittest.SkipTest('on windows \\ != / for path names')
        self.filestab.files_list[self.t_id] = (
            {'index': 0, 'path': '1/test_10.txt', 'offset': 0, 'size': 13},
            {'index': 1, 'path': '2/test_100.txt', 'offset': 13, 'size': 14},
        )
        self.filestab.update_files()
        self.filestab._on_torrentfilerenamed_event(
            self.t_id, self.index, '1/test_100.txt'
        )

        ret = self.verify_treestore(
            self.filestab.treestore, [['1/', [['test_100.txt'], ['test_10.txt']]]]
        )
        if not ret:
            self.print_treestore('Treestore not expected:', self.filestab.treestore)
        self.assertTrue(ret)
