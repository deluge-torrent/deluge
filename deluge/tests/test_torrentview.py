import gobject
from twisted.trial import unittest

import deluge.common
import deluge.component as component
from deluge.ui.gtkui.mainwindow import MainWindow
from deluge.ui.gtkui.menubar import MenuBar
from deluge.ui.gtkui.torrentdetails import TorrentDetails
from deluge.ui.gtkui.torrentview import TorrentView

deluge.common.setup_translations()


class TorrentviewTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        self.mainwindow = MainWindow()
        self.torrentview = TorrentView()
        self.torrentdetails = TorrentDetails()
        self.menubar = MenuBar()

    def tearDown(self):  # NOQA
        def on_shutdown(result):
            component._ComponentRegistry.components = {}
        return component.shutdown().addCallback(on_shutdown)

    def test_torrentview_columns(self):

        default_column_index = ['filter', 'torrent_id', 'dirty', '#', u'Name', u'Size',
                                u'Downloaded', u'Uploaded', u'Remaining', u'Progress',
                                u'Seeds', u'Peers', u'Seeds:Peers', u'Down Speed',
                                u'Up Speed', u'Down Limit', u'Up Limit', u'ETA', u'Ratio',
                                u'Avail', u'Added', u'Completed', u'Complete Seen',
                                u'Tracker', u'Download Folder', u'Owner', u'Shared']
        default_liststore_columns = [bool, str, bool, int, str, str, gobject.TYPE_UINT64,
                                     gobject.TYPE_UINT64, gobject.TYPE_UINT64, gobject.TYPE_UINT64,
                                     float, str, int, int, int, int, float, float, float,
                                     float, float, int, float, float, float, float,
                                     float, str, str, str, str, bool]
        self.assertEquals(self.torrentview.column_index, default_column_index)
        self.assertEquals(self.torrentview.liststore_columns, default_liststore_columns)

    def test_addcolumn_verify_index(self):

        self.assertEquals(self.torrentview.columns["Download Folder"].column_indices, [29])
        test_col = "Test column"
        self.torrentview.add_text_column(test_col, status_field=["label"])
        self.assertEquals(len(self.torrentview.liststore_columns), 33)
        self.assertEquals(len(self.torrentview.column_index), 28)
        self.assertEquals(self.torrentview.column_index[-1], test_col)
        self.assertEquals(self.torrentview.columns[test_col].column_indices, [32])

        test_col2 = "Test column2"
        self.torrentview.add_text_column(test_col2, status_field=["label2"])
        self.assertEquals(len(self.torrentview.liststore_columns), 34)
        self.assertEquals(len(self.torrentview.column_index), 29)
        self.assertEquals(self.torrentview.column_index[-1], test_col2)
        self.assertEquals(self.torrentview.columns[test_col2].column_indices, [33])

        self.torrentview.remove_column(test_col)
        self.assertEquals(len(self.torrentview.liststore_columns), 33)
        self.assertEquals(len(self.torrentview.column_index), 28)
        self.assertEquals(self.torrentview.column_index[-1], test_col2)
        self.assertEquals(self.torrentview.columns[test_col2].column_indices, [32])
