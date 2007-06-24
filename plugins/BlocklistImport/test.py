import unittest
from text import TextReader, GZMuleReader


class ImportTests(unittest.TestCase):

    def testpgtext(self):
        tr = TextReader("pg.txt")
        ips = tr.next()
        self.assertEqual("3.0.0.0", ips[0])
        self.assertEqual("3.255.255.255", ips[1])

    def testMule(self):
        mr = GZMuleReader("nipfilter.dat.gz")
        ips = mr.next()
        self.assertEqual("0.0.0.0", ips[0])
        self.assertEqual("3.255.255.255", ips[1])

if __name__ == '__main__':
    unittest.main()
