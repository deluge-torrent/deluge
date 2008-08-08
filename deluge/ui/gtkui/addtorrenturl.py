#
# addtorrenturl.py
#
# Copyright (C) 2007 Marcos Pinto ('markybob') <markybob@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
# 
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.

import pygtk
pygtk.require('2.0')
import gtk
import gettext

import deluge.common
import pkg_resources

class AddTorrentUrl:
    def __init__(self, parent=None):
        """Set up url dialog"""
        self.dlg = gtk.Dialog(_("Add torrent from URL"), None, 0, \
          (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.dlg.set_default_response(gtk.RESPONSE_OK)
        self.dlg.set_icon(deluge.common.get_logo(32))
        self.dlg.set_default_response(1)
        label = gtk.Label(_("Enter the URL of the .torrent to download"))
        self.entry = gtk.Entry()
        self.entry.connect("activate", lambda w : self.dlg.response\
            (gtk.RESPONSE_OK))
        self.dlg.vbox.pack_start(label)
        self.dlg.vbox.pack_start(self.entry)
        if deluge.common.windows_check():
            import win32clipboard as clip 
            import win32con
            clip.OpenClipboard() 
            text = clip.GetClipboardData(win32con.CF_UNICODETEXT) 
            clip.CloseClipboard() 
        else:
            clip = gtk.clipboard_get(selection='PRIMARY')
            text = clip.wait_for_text()
        if text:
            text = text.strip()
            if deluge.common.is_url(text):
                self.entry.set_text(text)

    def run(self):
        """Show url dialog and add torrent"""
        self.dlg.show_all()
        self.response = self.dlg.run()
        if self.response == gtk.RESPONSE_OK:
            url = self.entry.get_text().decode("utf_8")
            self.dlg.destroy()
            return url
        else:
            self.dlg.destroy()
            return None
