import gobject

from twisted.trial import unittest

from deluge.ui.gtkui.torrentview import TorrentView
from deluge.ui.gtkui.mainwindow import MainWindow
from deluge.ui.gtkui.torrentdetails import TorrentDetails
from deluge.ui.gtkui.menubar import MenuBar



class TorrentviewTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        pass

    def tearDown(self):  # NOQA
        pass

    def test_torrentview_columns(self):
        self.mainwindow = MainWindow()
        self.torrentview = TorrentView()
        self.torrentdetails = TorrentDetails()
        self.menubar = MenuBar()

        default_column_index = ['filter', 'torrent_id', 'dirty', '#', 'Name', 'Size', 'Downloaded', 'Uploaded', 'Progress', 'Seeders', 'Peers', 'Seeders/Peers', 'Down Speed', 'Up Speed', 'Down Limit', 'Up Limit', 'ETA', 'Ratio', 'Avail', 'Added', 'Tracker', 'Save Path']
        default_liststore_columns = [bool, str, bool, int, str, str, gobject.TYPE_UINT64, gobject.TYPE_UINT64, gobject.TYPE_UINT64, float, str, int, int, int, int, float, float, float, float, float, int, float, float, float, str, str, str]

        self.assertEquals(self.torrentview.column_index, default_column_index)
        self.assertEquals(self.torrentview.liststore_columns, default_liststore_columns)

        self.assertEquals(self.torrentview.columns["Save Path"].column_indices, [26])
        test_col = "Test column"
        self.torrentview.add_text_column(test_col, status_field=["label"])
        self.assertEquals(len(self.torrentview.liststore_columns), 28)
        self.assertEquals(len(self.torrentview.column_index), 23)
        self.assertEquals(self.torrentview.column_index[-1], test_col)
        self.assertEquals(self.torrentview.columns[test_col].column_indices, [27])

        test_col2 = "Test column2"
        self.torrentview.add_text_column(test_col2, status_field=["label2"])
        self.assertEquals(len(self.torrentview.liststore_columns), 29)
        self.assertEquals(len(self.torrentview.column_index), 24)
        self.assertEquals(self.torrentview.column_index[-1], test_col2)
        self.assertEquals(self.torrentview.columns[test_col2].column_indices, [28])

        self.torrentview.remove_column(test_col)
        self.assertEquals(len(self.torrentview.liststore_columns), 28)
        self.assertEquals(len(self.torrentview.column_index), 23)
        self.assertEquals(self.torrentview.column_index[-1], test_col2)
        self.assertEquals(self.torrentview.columns[test_col2].column_indices, [27])
