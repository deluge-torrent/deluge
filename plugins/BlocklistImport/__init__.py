##
# Copyright 2007 Steve 'Tarka' Smith (tarka@internode.on.net)
# Distributed under the same terms as Deluge
##

plugin_name = "Blocklist Importer"
plugin_author = "Steve 'Tarka' Smith"
plugin_version = "0.4"
plugin_description = _("""
Download and import various IP blocklists.

Currently this plugin can handle PeerGuardian (binary and text),
SafePeer and Emule lists.  PeerGuardian 7zip format files are not
supported.  Files may be specified as URLs or locations on the local
filesystem.

A page with pointer to blocklist download sites is available on the
wiki:

http://dev.deluge-torrent.org/wiki/BlocklistPlugin
""")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return BlocklistImport(path, core, interface)

#################### The plugin itself ####################

import urllib, deluge.common, deluge.pref
from peerguardian import PGReader, PGException
from text import TextReader, GZMuleReader, PGZip
from ui import GTKConfig, GTKProgress

# List of formats supported.  This is used to generate the UI list and
# specify the reader class.  The last entry is for storage by the UI.
readers = {'p2bgz':[_("PeerGuardian P2B (GZip)"), PGReader, None],
           'pgtext':[_("PeerGuardian Text (Uncompressed)"), TextReader, None],
           'gzmule':[_("Emule IP list (GZip)"), GZMuleReader, None],
           'spzip':[_("SafePeer Text (Zipped)"), PGZip, None]}

class BlocklistImport:

    def __init__(self, path, core, interface):
        print "Loading blocklist plugin ..."
        # Save the path, interface, and core so they can be used later
        self.path = path
        self.core = core
        self.interface = interface
        self.cancelled = False
        self.gtkconf = GTKConfig(self)
        self.gtkprog = GTKProgress(self)
        self.nimported = 0

        self.blockfile = deluge.common.CONFIG_DIR + "/blocklist.cache"

        conffile = deluge.common.CONFIG_DIR + "/blocklist.conf"
        self.config = deluge.pref.Preferences(filename=conffile,
                                              global_defaults=False)
        self.config.load()

        if self.config.has_key('url'):
            self.loadlist(fetch=self.config.get('load_on_start'))


    def _download_update(self, curr, chunksize, size):
        incs = float(size) / float(chunksize)
        self.gtkprog.download_prog(curr/incs)

    def loadlist(self, fetch=False):
        # Stop all torrents
        self.paused_or_not = {}
        for unique_ID in self.core.unique_IDs:
            self.paused_or_not[unique_ID] = self.core.is_user_paused(unique_ID)
            if not self.paused_or_not[unique_ID]:
                self.core.set_user_pause(unique_ID, True, enforce_queue=False)

        self.gtkprog.start()

        # Attempt initial import
        if fetch:
            print "Fetching",self.config.get('url')
            self.gtkprog.start_download()
            try:
                filename, headers = urllib.urlretrieve(self.config.get('url'),
                                                    filename=self.blockfile,
                                                    reporthook=self._download_update)
            except IOError, e:
                err = ui.GTKError(_("Couldn't download URL") + ": %s"%e)
                self.gtkprog.stop()
                return

        self.gtkprog.start_import()

        self.core.reset_ip_filter()
        ltype = self.config.get('listtype')
        print "importing with",ltype

        try:
            reader = readers[ltype][1](self.blockfile)
        except IOError, e:
            err = ui.GTKError(_("Couldn't open blocklist file") + ": %s"%e)
            self.gtkprog.stop()
            return

        print "Starting import"
        try:
            ips = reader.next()
        except:
            ui.GTKError(_("Wrong file type or corrupted blocklist file."))
        curr = 0
        try:
            while ips and not self.cancelled:
                self.core.add_range_to_ip_filter(*ips)
                ips = reader.next()
                curr += 1
                if curr % 100 == 0:
                    self.gtkprog.import_prog(text=(_("Imported") + " %s " + _("IPs"))%curr)
                else:
	            self.gtkprog.import_prog()

        except:
            self.gtkprog.stop()
            reader.close()
            return

        self.core.set_ip_filter()
        reader.close()
        self.nimported = curr
        self.gtkprog.end_import()
        print "Import finished"

        self.gtkprog.stop()
        self.cancelled = False
        #restart torrents that werent paused by us
        for unique_ID in self.core.unique_IDs:
            if not self.paused_or_not[unique_ID]:
                self.core.set_user_pause(unique_ID, False, enforce_queue=False)

    def configure(self, window):
        self.gtkconf.start(self.config.get('listtype'),
                           self.config.get('url'),
                           self.config.get('load_on_start'),
                           window)

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
        msg = ("[" + _("Blocklist") + ": %s " + _("entries") + "]") % self.nimported
        self.interface.statusbar_temp_msg += '   ' + msg
