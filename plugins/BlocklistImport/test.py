import unittest
from text import TextReader, GZMuleReader, PGZip


class ImportTests(unittest.TestCase):

    def testpgtext(self):
        fr = TextReader("pg.txt")
        ips = fr.next()
        self.assertEqual("3.0.0.0", ips[0])
        self.assertEqual("3.255.255.255", ips[1])

    def testMule(self):
        fr = GZMuleReader("nipfilter.dat.gz")
        ips = fr.next()
        self.assertEqual("0.0.0.0", ips[0])
        self.assertEqual("3.255.255.255", ips[1])

    def testZip(self):
        fr = PGZip("splist.zip")
        ips = fr.next()
        print "wibble wibble",ips
        self.assertEqual("1.1.1.1", ips[0])
        self.assertEqual("3.255.255.255", ips[1])

        ips = fr.next()
        self.assertEqual("0.0.0.0", ips[0])
        self.assertEqual("3.255.255.255", ips[1])

        ips = fr.next()
        self.assertEqual(ips, False)

if __name__ == '__main__':
    unittest.main()
