##
# Copyright 2007 Steve 'Tarka' Smith (tarka@internode.on.net)
# Distributed under the same terms as Deluge
##

plugin_name = "Blocklist Importer"
plugin_author = "Steve 'Tarka' Smith"
plugin_version = "0.3"
plugin_description = """
Downloads and import PeerGuardian blocklists.

It can parse uncompressed text-format list, and Gzip P2B version 1 and
2.  It does not currently support 7zip encoded lists unfortunately.
It is suggested these are downloaded an unpacked via a cron script.
"""

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return BlocklistImport(path, core, interface)

#################### The plugin itself ####################

import urllib, deluge.common, deluge.pref
from peerguardian import PGReader, PGException
from text import TextReader, GZMuleReader
from ui import GTKConfig, GTKProgress

# List of formats supported.  This is used to generate the UI list and
# specify the reader class
readers = {'p2bgz':("PeerGuardian P2B (GZip)", PGReader),
           'pgtext':("PeerGuardian Text (Uncompressed)", TextReader),
           'gzmule':("Emule IP list (GZip)", GZMuleReader)}

class BlocklistImport:

    def __init__(self, path, core, interface):
        print "Loading blocklist plugin ..."
        # Save the path, interface, and core so they can be used later
        self.path = path
        self.core = core
        self.interface = interface
        self.gtkconf = GTKConfig(self)
        self.gtkprog = GTKProgress(self)
        self.cancelled = False

        self.blockfile = deluge.common.CONFIG_DIR + "/blocklist.cache"

        conffile = deluge.common.CONFIG_DIR + "/blocklist.conf"
        self.config = deluge.pref.Preferences(filename=conffile,
                                              global_defaults=False)
        self.config.load()

        if not self.config.has_key('url'):
            self.configure()
        else:
            self.loadlist(fetch=self.config.get('load_on_start'))


    def _download_update(self, curr, chunksize, size):
        incs = float(size) / float(chunksize)
        self.gtkprog.download_prog(curr/incs)

    def loadlist(self, fetch=False):
        self.gtkprog.start()
        
        # Attempt initial import
        if fetch:
            print "Fetching",self.config.get('url')
            self.gtkprog.start_download()
            try:
	            filename, headers = urllib.urlretrieve(self.config.get('url'),
                                                   filename=self.blockfile,
                                                   reporthook=self._download_update)
            except IOError, (errno, strerr):
                err = ui.GTKError("Couldn't download URL: %s"%strerr)
                self.gtkprog.stop()
                return

        self.gtkprog.start_import()

        self.core.reset_ip_filter()
        ltype = self.config.get('listtype')
        print "importing with",ltype

        try:
        reader = readers[ltype][1](self.blockfile)
        except IOError, (errno, strerr):
            err = ui.GTKError("Couldn't open blocklist file: %s"%strerr)
            self.gtkprog.stop()
            return

        print "Starting import"
        ips = reader.next()
        curr = 0
        while ips and not self.cancelled:
            self.core.add_range_to_ip_filter(*ips)
            ips = reader.next()
            curr += 1
            if curr % 100 == 0:
                self.gtkprog.import_prog(text="Imported %s IPs"%curr)
            else:
            self.gtkprog.import_prog()

        reader.close()
        self.gtkprog.end_import()
        print "Import complete"

        self.gtkprog.stop()

    def configure(self):
        self.gtkconf.start()

    def setconfig(self, url, load_on_start, listtype):
        self.config.set('url', url)
        self.config.set('load_on_start', load_on_start)
        self.config.set('listtype', listtype)
        self.config.save()

        self.loadlist(fetch=True)

    def disable(self):
        self.core.reset_ip_filter()

    def unload(self):
        self.core.reset_ip_filter()

    def update(self):
        pass
