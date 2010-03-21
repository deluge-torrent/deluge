from twisted.trial import unittest
from deluge.common import VersionSplit

class VersionSplitTestClass(unittest.TestCase):
    def test_compare(self):
        vs1 = VersionSplit("0.14.9")
        vs2 = VersionSplit("0.14.10")
        vs3 = VersionSplit("0.14.5")

        self.assertTrue(vs1 > vs3)
        self.assertTrue(vs2 > vs1)
