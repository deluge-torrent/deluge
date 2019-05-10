# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bro <bro.development@gmail.com>
# Copyright (C) 2014 Calum Lind <calumlind@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import pytest
from twisted.trial import unittest

import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.i18n import setup_translation

from . import common
from .basetest import BaseTestCase

# Allow running other tests without GTKUI dependencies available
try:
    # pylint: disable=ungrouped-imports
    from gi.repository.GObject import TYPE_UINT64

    from deluge.ui.gtk3.gtkui import DEFAULT_PREFS
    from deluge.ui.gtk3.mainwindow import MainWindow
    from deluge.ui.gtk3.menubar import MenuBar
    from deluge.ui.gtk3.torrentdetails import TorrentDetails
    from deluge.ui.gtk3.torrentview import TorrentView
except (ImportError, ValueError):
    libs_available = False
    TYPE_UINT64 = 'Whatever'
else:
    libs_available = True

setup_translation()


@pytest.mark.gtkui
class TorrentviewTestCase(BaseTestCase):

    default_column_index = [
        'filter',
        'torrent_id',
        'dirty',
        '#',
        'Name',
        'Size',
        'Downloaded',
        'Uploaded',
        'Remaining',
        'Progress',
        'Seeds',
        'Peers',
        'Seeds:Peers',
        'Down Speed',
        'Up Speed',
        'Down Limit',
        'Up Limit',
        'ETA',
        'Ratio',
        'Avail',
        'Added',
        'Completed',
        'Complete Seen',
        'Tracker',
        'Download Folder',
        'Owner',
        'Shared',
    ]
    default_liststore_columns = [
        bool,
        str,
        bool,
        int,
        str,
        str,  # Name
        TYPE_UINT64,
        TYPE_UINT64,
        TYPE_UINT64,
        TYPE_UINT64,
        float,
        str,  # Progress
        int,
        int,
        int,
        int,
        float,  # Seeds, Peers
        int,
        int,
        float,
        float,
        int,
        float,
        float,  # ETA, Ratio, Avail
        int,
        int,
        int,
        str,
        str,  # Tracker
        str,
        str,
        bool,
    ]  # shared

    def set_up(self):
        if libs_available is False:
            raise unittest.SkipTest('GTKUI dependencies not available')

        common.set_tmp_config_dir()
        # MainWindow loads this config file, so lets make sure it contains the defaults
        ConfigManager('gtk3ui.conf', defaults=DEFAULT_PREFS)
        self.mainwindow = MainWindow()
        self.torrentview = TorrentView()
        self.torrentdetails = TorrentDetails()
        self.menubar = MenuBar()

    def tear_down(self):
        return component.shutdown()

    def test_torrentview_columns(self):

        self.assertEqual(
            self.torrentview.column_index, TorrentviewTestCase.default_column_index
        )
        self.assertEqual(
            self.torrentview.liststore_columns,
            TorrentviewTestCase.default_liststore_columns,
        )
        self.assertEqual(
            self.torrentview.columns['Download Folder'].column_indices, [29]
        )

    def test_add_column(self):

        # Add a text column
        test_col = 'Test column'
        self.torrentview.add_text_column(test_col, status_field=['label'])
        self.assertEqual(
            len(self.torrentview.liststore_columns),
            len(TorrentviewTestCase.default_liststore_columns) + 1,
        )
        self.assertEqual(
            len(self.torrentview.column_index),
            len(TorrentviewTestCase.default_column_index) + 1,
        )
        self.assertEqual(self.torrentview.column_index[-1], test_col)
        self.assertEqual(self.torrentview.columns[test_col].column_indices, [32])

    def test_add_columns(self):

        # Add a text column
        test_col = 'Test column'
        self.torrentview.add_text_column(test_col, status_field=['label'])

        # Add a second text column
        test_col2 = 'Test column2'
        self.torrentview.add_text_column(test_col2, status_field=['label2'])

        self.assertEqual(
            len(self.torrentview.liststore_columns),
            len(TorrentviewTestCase.default_liststore_columns) + 2,
        )
        self.assertEqual(
            len(self.torrentview.column_index),
            len(TorrentviewTestCase.default_column_index) + 2,
        )
        # test_col
        self.assertEqual(self.torrentview.column_index[-2], test_col)
        self.assertEqual(self.torrentview.columns[test_col].column_indices, [32])

        # test_col2
        self.assertEqual(self.torrentview.column_index[-1], test_col2)
        self.assertEqual(self.torrentview.columns[test_col2].column_indices, [33])

    def test_remove_column(self):

        # Add and remove text column
        test_col = 'Test column'
        self.torrentview.add_text_column(test_col, status_field=['label'])
        self.torrentview.remove_column(test_col)

        self.assertEqual(
            len(self.torrentview.liststore_columns),
            len(TorrentviewTestCase.default_liststore_columns),
        )
        self.assertEqual(
            len(self.torrentview.column_index),
            len(TorrentviewTestCase.default_column_index),
        )
        self.assertEqual(
            self.torrentview.column_index[-1],
            TorrentviewTestCase.default_column_index[-1],
        )
        self.assertEqual(
            self.torrentview.columns[
                TorrentviewTestCase.default_column_index[-1]
            ].column_indices,
            [31],
        )

    def test_remove_columns(self):

        # Add two columns
        test_col = 'Test column'
        self.torrentview.add_text_column(test_col, status_field=['label'])
        test_col2 = 'Test column2'
        self.torrentview.add_text_column(test_col2, status_field=['label2'])

        # Remove test_col
        self.torrentview.remove_column(test_col)
        self.assertEqual(
            len(self.torrentview.liststore_columns),
            len(TorrentviewTestCase.default_liststore_columns) + 1,
        )
        self.assertEqual(
            len(self.torrentview.column_index),
            len(TorrentviewTestCase.default_column_index) + 1,
        )
        self.assertEqual(self.torrentview.column_index[-1], test_col2)
        self.assertEqual(self.torrentview.columns[test_col2].column_indices, [32])

        # Remove test_col2
        self.torrentview.remove_column(test_col2)
        self.assertEqual(
            len(self.torrentview.liststore_columns),
            len(TorrentviewTestCase.default_liststore_columns),
        )
        self.assertEqual(
            len(self.torrentview.column_index),
            len(TorrentviewTestCase.default_column_index),
        )
        self.assertEqual(
            self.torrentview.column_index[-1],
            TorrentviewTestCase.default_column_index[-1],
        )
        self.assertEqual(
            self.torrentview.columns[
                TorrentviewTestCase.default_column_index[-1]
            ].column_indices,
            [31],
        )

    def test_add_remove_column_multiple_types(self):

        # Add a column with multiple column types
        test_col3 = 'Test column3'
        self.torrentview.add_progress_column(
            test_col3, status_field=['progress', 'label3'], col_types=[float, str]
        )
        self.assertEqual(
            len(self.torrentview.liststore_columns),
            len(TorrentviewTestCase.default_liststore_columns) + 2,
        )
        self.assertEqual(
            len(self.torrentview.column_index),
            len(TorrentviewTestCase.default_column_index) + 1,
        )
        self.assertEqual(self.torrentview.column_index[-1], test_col3)
        self.assertEqual(self.torrentview.columns[test_col3].column_indices, [32, 33])

        # Remove multiple column-types column
        self.torrentview.remove_column(test_col3)

        self.assertEqual(
            len(self.torrentview.liststore_columns),
            len(TorrentviewTestCase.default_liststore_columns),
        )
        self.assertEqual(
            len(self.torrentview.column_index),
            len(TorrentviewTestCase.default_column_index),
        )
        self.assertEqual(
            self.torrentview.column_index[-1],
            TorrentviewTestCase.default_column_index[-1],
        )
        self.assertEqual(
            self.torrentview.columns[
                TorrentviewTestCase.default_column_index[-1]
            ].column_indices,
            [31],
        )
