#
# Copyright (C) 2014 Bro <bro.development@gmail.com>
# Copyright (C) 2014 Calum Lind <calumlind@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import pytest

import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.conftest import BaseTestCase
from deluge.i18n import setup_translation

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
class TestTorrentview(BaseTestCase):
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
        'Last Transfer',
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
        int,
        str,
        str,  # Tracker
        str,
        str,
        bool,
    ]  # shared

    def set_up(self):
        if libs_available is False:
            pytest.skip('GTKUI dependencies not available')

        # MainWindow loads this config file, so lets make sure it contains the defaults
        ConfigManager('gtk3ui.conf', defaults=DEFAULT_PREFS)
        self.mainwindow = MainWindow()
        self.torrentview = TorrentView()
        self.torrentdetails = TorrentDetails()
        self.menubar = MenuBar()

    def tear_down(self):
        return component.shutdown()

    def test_torrentview_columns(self):
        assert self.torrentview.column_index == self.default_column_index
        assert self.torrentview.liststore_columns == self.default_liststore_columns
        assert self.torrentview.columns['Download Folder'].column_indices == [30]

    def test_add_column(self):
        # Add a text column
        test_col = 'Test column'
        self.torrentview.add_text_column(test_col, status_field=['label'])
        assert (
            len(self.torrentview.liststore_columns)
            == len(self.default_liststore_columns) + 1
        )
        assert len(self.torrentview.column_index) == len(self.default_column_index) + 1
        assert self.torrentview.column_index[-1] == test_col
        assert self.torrentview.columns[test_col].column_indices == [33]

    def test_add_columns(self):
        # Add a text column
        test_col = 'Test column'
        self.torrentview.add_text_column(test_col, status_field=['label'])

        # Add a second text column
        test_col2 = 'Test column2'
        self.torrentview.add_text_column(test_col2, status_field=['label2'])

        assert (
            len(self.torrentview.liststore_columns)
            == len(self.default_liststore_columns) + 2
        )
        assert len(self.torrentview.column_index) == len(self.default_column_index) + 2
        # test_col
        assert self.torrentview.column_index[-2] == test_col
        assert self.torrentview.columns[test_col].column_indices == [33]

        # test_col2
        assert self.torrentview.column_index[-1] == test_col2
        assert self.torrentview.columns[test_col2].column_indices == [34]

    def test_remove_column(self):
        # Add and remove text column
        test_col = 'Test column'
        self.torrentview.add_text_column(test_col, status_field=['label'])
        self.torrentview.remove_column(test_col)

        assert len(self.torrentview.liststore_columns) == len(
            self.default_liststore_columns
        )
        assert len(self.torrentview.column_index) == len(self.default_column_index)
        assert self.torrentview.column_index[-1] == self.default_column_index[-1]
        assert self.torrentview.columns[
            self.default_column_index[-1]
        ].column_indices == [32]

    def test_remove_columns(self):
        # Add two columns
        test_col = 'Test column'
        self.torrentview.add_text_column(test_col, status_field=['label'])
        test_col2 = 'Test column2'
        self.torrentview.add_text_column(test_col2, status_field=['label2'])

        # Remove test_col
        self.torrentview.remove_column(test_col)
        assert (
            len(self.torrentview.liststore_columns)
            == len(self.default_liststore_columns) + 1
        )
        assert len(self.torrentview.column_index) == len(self.default_column_index) + 1
        assert self.torrentview.column_index[-1] == test_col2
        assert self.torrentview.columns[test_col2].column_indices == [33]

        # Remove test_col2
        self.torrentview.remove_column(test_col2)
        assert len(self.torrentview.liststore_columns) == len(
            self.default_liststore_columns
        )
        assert len(self.torrentview.column_index) == len(self.default_column_index)
        assert self.torrentview.column_index[-1] == self.default_column_index[-1]
        assert self.torrentview.columns[
            self.default_column_index[-1]
        ].column_indices == [32]

    def test_add_remove_column_multiple_types(self):
        # Add a column with multiple column types
        test_col3 = 'Test column3'
        self.torrentview.add_progress_column(
            test_col3, status_field=['progress', 'label3'], col_types=[float, str]
        )
        assert (
            len(self.torrentview.liststore_columns)
            == len(self.default_liststore_columns) + 2
        )
        assert len(self.torrentview.column_index) == len(self.default_column_index) + 1
        assert self.torrentview.column_index[-1] == test_col3
        assert self.torrentview.columns[test_col3].column_indices == [33, 34]

        # Remove multiple column-types column
        self.torrentview.remove_column(test_col3)

        assert len(self.torrentview.liststore_columns) == len(
            self.default_liststore_columns
        )
        assert len(self.torrentview.column_index) == len(self.default_column_index)
        assert self.torrentview.column_index[-1] == self.default_column_index[-1]
        assert self.torrentview.columns[
            self.default_column_index[-1]
        ].column_indices == [32]
