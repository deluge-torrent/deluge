

plugin_name = "Blocklist Importer"
plugin_author = "Steve 'Tarka' Smith"
plugin_version = "0.1"
plugin_description = "Downloads and import PeerGuardian blocklists"

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return BlocklistImport(path, core, interface)

#################### The plugin itself ####################

import urllib, deluge.common, deluge.pref
from peerguardian import PGReader, PGException
from ui import GTKConfig, GTKProgress

class BlocklistImport:

    def __init__(self, path, core, interface):
        print "Loading blocklist plugin ..."
        # Save the path, interface, and core so they can be used later
        self.path = path
        self.core = core
        self.interface = interface
        self.gtkconf = GTKConfig(self)
        self.gtkprog = GTKProgress(self)

        self.blockfile = deluge.common.CONFIG_DIR + "/blocklist.p2b.gzip"

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
        # FIXME
        #self.gtkprog.start()
        
        # Attempt initial import
        # FIXME: Make async
        if fetch:
            print "Downloading blocklist..."
            filename, headers = urllib.urlretrieve(self.config.get('url'),
                                                   filename=self.blockfile,
                                                   reporthook=self._download_update)
            print "Done"

        self.core.reset_ip_filter()
        reader = PGReader(self.blockfile)

        ips = reader.next()
        while ips:
            print "Blocking",ips
            self.core.add_range_to_ip_filter(*ips)
            ips = reader.next()

        reader.close()

        # FIXME
        #self.gtkprog.stop()

    def configure(self):
        self.gtkconf.start()

    def setconfig(self, url, load_on_start):
        self.config.set('url', url)
        self.config.set('load_on_start', load_on_start)
        self.config.save()

        self.loadlist(fetch=True)

    def disable(self):
        self.core.reset_ip_filter()

    def unload(self):
        #self.config.save_to_file(self.config_file)
        self.core.reset_ip_filter()

    def update(self):
        pass
