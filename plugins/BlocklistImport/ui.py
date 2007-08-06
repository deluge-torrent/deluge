##
# Copyright 2007 Steve 'Tarka' Smith (tarka@internode.on.net)
# Distributed under the same terms as Deluge
##

import gobject, gtk
import BlocklistImport

class GTKConfig(gtk.Dialog):
    def __init__(self, plugin):
        gtk.Dialog.__init__(self, title="Blocklist Config",
                            flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                     gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.set_property("skip-taskbar-hint", True)
        self.set_property("skip-pager-hint", True)

        self.plugin = plugin
        # Setup
        self.set_border_width(12)
        self.vbox.set_spacing(6)

        # List source
        label = gtk.Label()
        label.set_markup('<b>' + _("Blocklist URL") + '</b>')
        self.url = gtk.Entry()

        ls = gtk.ListStore(gobject.TYPE_STRING,  # Long name
                           gobject.TYPE_STRING)  # Short name
        for k in BlocklistImport.readers.keys():
            i = ls.append([BlocklistImport.readers[k][0], k])
            BlocklistImport.readers[k][2] = ls.get_path(i)

        cell = gtk.CellRendererText()
        cell.set_property('xpad', 5) # padding for status text

        self.listtype = gtk.ComboBox(model=ls)
        self.listtype.pack_start(cell, False)
        self.listtype.add_attribute(cell, 'text', 0)
        self.listtype.set_active(0)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(label)
        hbox.pack_start(self.url)

        self.vbox.pack_start(self.listtype)
        self.vbox.pack_start(hbox)

        # Load on start
        self.load_on_start = gtk.CheckButton(_("Download on start"))
        self.vbox.pack_start(self.load_on_start)

        self.connect('response', self.ok)
        self.connect('close', self.cancel)

        self.hide_all()


    def ok(self, dialog, response):
        self.hide_all()

        if response != gtk.RESPONSE_ACCEPT:
            self.cancel(dialog)
            return

        ls = self.listtype.get_model()
        ltype = ls[self.listtype.get_active()][1]
        url = self.url.get_text()
        los = self.load_on_start.get_active()
        
        self.plugin.setconfig(url, los, ltype)


    def cancel(self, dialog):
        self.hide_all()

    def start(self, ltype, url, load, window):
        self.set_transient_for(window)
        if ltype:
            path = BlocklistImport.readers[ltype][2]
            i = self.listtype.get_model().get_iter(path)
            self.listtype.set_active_iter(i)
            
        if url:
            self.url.set_text(url)

        if load:
            self.load_on_start.set_active(load)

        self.show_all()


class GTKProgress(gtk.Dialog):
    def __init__(self, plugin):
        gtk.Dialog.__init__(self, title="Loading Blocklist",
                            flags=gtk.DIALOG_MODAL,
                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        self.plugin = plugin

        # Setup
        self.set_border_width(12)
        self.vbox.set_spacing(6)

        label = gtk.Label()
        label.set_markup('<b>' + _("Loading and installing blocklist") + '</b>')
        self.vbox.pack_start(label)

        self.progress = gtk.ProgressBar()
        self.vbox.pack_start(self.progress)

        self.connect('response', self.response)
        self.connect('close', self.cancel)

        self.hide_all()

    def start_download(self):
        self.progress.set_text(_("Downloading"))
        self.progress.set_fraction(0.0)
        self.update()

    def download_prog(self, fract):
        if fract > 1.0:
            fract = 1.0
        self.progress.set_fraction(fract)
        self.update()

    def start_import(self):
        self.progress.set_text(_("Importing"))
        self.progress.set_fraction(0.0)
        self.progress.set_pulse_step(0.0075)
        self.update()

    def import_prog(self, text=None):
        if text:
            self.progress.set_text(text)
        self.update()

    def end_import(self):
        self.progress.set_text(_("Complete"))
        self.progress.set_fraction(1.0)
        self.update()


    def response(self, dialog, response):
        self.cancel(dialog)

    def cancel(self, dialog):
        print "Cancelling"
        self.plugin.cancelled = True
        self.hide_all()

    def start(self):
        self.show_all()
        self.update()

    def stop(self):
        self.hide_all()

    def update(self):
        while gtk.events_pending():
            not gtk.main_iteration(block=True)


class GTKError(gtk.Dialog):
    def __init__(self, message):
        gtk.Dialog.__init__(self, title="Error",
                            flags=gtk.DIALOG_MODAL,
                            buttons=(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        # Setup
        self.set_border_width(12)
        self.vbox.set_spacing(6)

        # List source
        label = gtk.Label()
        label.set_text(message)
        self.vbox.pack_start(label)

        self.connect('response', self.ok)
        self.connect('close', self.cancel)

        self.show_all()

    def ok(self, dialog, response):
        self.hide_all()

    def cancel(self, dialog):
        self.hide_all()
