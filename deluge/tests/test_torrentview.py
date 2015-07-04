import pytest
from twisted.trial import unittest

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager

from . import common
from .basetest import BaseTestCase

libs_available = True
# Allow running other tests without GTKUI dependencies available
try:
    from gi.repository.GObject import TYPE_UINT64
    from deluge.ui.gtkui.mainwindow import MainWindow
    from deluge.ui.gtkui.menubar import MenuBar
    from deluge.ui.gtkui.torrentdetails import TorrentDetails
    from deluge.ui.gtkui.torrentview import TorrentView
    from deluge.ui.gtkui.gtkui import DEFAULT_PREFS
except ImportError as err:
    libs_available = False
    TYPE_UINT64 = "Whatever"
    import traceback
    traceback.print_exc()

deluge.common.setup_translations()


@pytest.mark.gtkui
class TorrentviewTestCase(BaseTestCase):

    default_column_index = ['filter', 'torrent_id', 'dirty', '#', u'Name', u'Size',
                            u'Downloaded', u'Uploaded', u'Remaining', u'Progress',
                            u'Seeds', u'Peers', u'Seeds:Peers', u'Down Speed',
                            u'Up Speed', u'Down Limit', u'Up Limit', u'ETA', u'Ratio',
                            u'Avail', u'Added', u'Completed', u'Complete Seen',
                            u'Tracker', u'Download Folder', u'Owner', u'Shared']
    default_liststore_columns = [bool, str, bool, int, str, str, TYPE_UINT64,
                                 TYPE_UINT64, TYPE_UINT64, TYPE_UINT64,
                                 float, str, int, int, int, int, float, float, float,
                                 float, float, int, float, float, float, float,
                                 float, str, str, str, str, bool]

    def set_up(self):
        if libs_available is False:
            raise unittest.SkipTest("GTKUI dependencies not available")

        common.set_tmp_config_dir()
        # MainWindow loads this config file, so lets make sure it contains the defaults
        ConfigManager("gtkui.conf", defaults=DEFAULT_PREFS)
        self.mainwindow = MainWindow()
        self.torrentview = TorrentView()
        self.torrentdetails = TorrentDetails()
        self.menubar = MenuBar()

    def tear_down(self):
        return component.shutdown()

    def test_torrentview_columns(self):

        self.assertEquals(self.torrentview.column_index, TorrentviewTestCase.default_column_index)
        self.assertEquals(self.torrentview.liststore_columns, TorrentviewTestCase.default_liststore_columns)
        self.assertEquals(self.torrentview.columns["Download Folder"].column_indices, [29])

    def test_add_column(self):

        # Add a text column
        test_col = "Test column"
        self.torrentview.add_text_column(test_col, status_field=["label"])
        self.assertEquals(len(self.torrentview.liststore_columns),
                          len(TorrentviewTestCase.default_liststore_columns) + 1)
        self.assertEquals(len(self.torrentview.column_index),
                          len(TorrentviewTestCase.default_column_index) + 1)
        self.assertEquals(self.torrentview.column_index[-1], test_col)
        self.assertEquals(self.torrentview.columns[test_col].column_indices, [32])

    def test_add_columns(self):

        # Add a text column
        test_col = "Test column"
        self.torrentview.add_text_column(test_col, status_field=["label"])

        # Add a second text column
        test_col2 = "Test column2"
        self.torrentview.add_text_column(test_col2, status_field=["label2"])

        self.assertEquals(len(self.torrentview.liststore_columns),
                          len(TorrentviewTestCase.default_liststore_columns) + 2)
        self.assertEquals(len(self.torrentview.column_index),
                          len(TorrentviewTestCase.default_column_index) + 2)
        # test_col
        self.assertEquals(self.torrentview.column_index[-2], test_col)
        self.assertEquals(self.torrentview.columns[test_col].column_indices, [32])

        # test_col2
        self.assertEquals(self.torrentview.column_index[-1], test_col2)
        self.assertEquals(self.torrentview.columns[test_col2].column_indices, [33])

    def test_remove_column(self):

        # Add and remove text column
        test_col = "Test column"
        self.torrentview.add_text_column(test_col, status_field=["label"])
        self.torrentview.remove_column(test_col)

        self.assertEquals(len(self.torrentview.liststore_columns), len(TorrentviewTestCase.default_liststore_columns))
        self.assertEquals(len(self.torrentview.column_index), len(TorrentviewTestCase.default_column_index))
        self.assertEquals(self.torrentview.column_index[-1], TorrentviewTestCase.default_column_index[-1])
        self.assertEquals(self.torrentview.columns[TorrentviewTestCase.default_column_index[-1]].column_indices, [31])

    def test_remove_columns(self):

        # Add two columns
        test_col = "Test column"
        self.torrentview.add_text_column(test_col, status_field=["label"])
        test_col2 = "Test column2"
        self.torrentview.add_text_column(test_col2, status_field=["label2"])

        # Remove test_col
        self.torrentview.remove_column(test_col)
        self.assertEquals(len(self.torrentview.liststore_columns),
                          len(TorrentviewTestCase.default_liststore_columns) + 1)
        self.assertEquals(len(self.torrentview.column_index),
                          len(TorrentviewTestCase.default_column_index) + 1)
        self.assertEquals(self.torrentview.column_index[-1], test_col2)
        self.assertEquals(self.torrentview.columns[test_col2].column_indices, [32])

        # Remove test_col2
        self.torrentview.remove_column(test_col2)
        self.assertEquals(len(self.torrentview.liststore_columns), len(TorrentviewTestCase.default_liststore_columns))
        self.assertEquals(len(self.torrentview.column_index), len(TorrentviewTestCase.default_column_index))
        self.assertEquals(self.torrentview.column_index[-1], TorrentviewTestCase.default_column_index[-1])
        self.assertEquals(self.torrentview.columns[TorrentviewTestCase.default_column_index[-1]].column_indices, [31])

    def test_add_remove_column_multiple_types(self):

        # Add a column with multiple column types
        test_col3 = "Test column3"
        self.torrentview.add_progress_column(test_col3, status_field=["progress", "label3"], col_types=[float, str])
        self.assertEquals(len(self.torrentview.liststore_columns),
                          len(TorrentviewTestCase.default_liststore_columns) + 2)
        self.assertEquals(len(self.torrentview.column_index),
                          len(TorrentviewTestCase.default_column_index) + 1)
        self.assertEquals(self.torrentview.column_index[-1], test_col3)
        self.assertEquals(self.torrentview.columns[test_col3].column_indices, [32, 33])

        # Remove multiple column-types column
        self.torrentview.remove_column(test_col3)

        self.assertEquals(len(self.torrentview.liststore_columns), len(TorrentviewTestCase.default_liststore_columns))
        self.assertEquals(len(self.torrentview.column_index), len(TorrentviewTestCase.default_column_index))
        self.assertEquals(self.torrentview.column_index[-1], TorrentviewTestCase.default_column_index[-1])
        self.assertEquals(self.torrentview.columns[TorrentviewTestCase.default_column_index[-1]].column_indices, [31])
