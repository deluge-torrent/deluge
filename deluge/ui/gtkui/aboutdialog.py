#
# aboutdialog.py
#
# Copyright (C) 2007 Marcos Pinto ('markybob') <markybob@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
import pkg_resources

import deluge.common
from deluge.ui.client import aclient as client

class AboutDialog:
    def __init__(self):
        # Get the glade file for the about dialog
        def url_hook(dialog, url):
            client.open_url_in_browser(url)
        gtk.about_dialog_set_url_hook(url_hook)
        self.about = gtk.AboutDialog()
        self.about.set_position(gtk.WIN_POS_CENTER)
        self.about.set_name("Deluge")
        self.about.set_program_name("Deluge")

        # Get the version and revision numbers
        rev = deluge.common.get_revision()
        version = deluge.common.get_version()
        if rev != "":
            version = version + "r" + rev

        self.about.set_copyright("Copyright © 2007-2008 Andrew Resch")
        self.about.set_comments("A peer-to-peer file sharing program utilizing the Bittorrent protocol.")
        self.about.set_version(version)
        self.about.set_authors(["Andrew Resch", "Marcos Pinto", 
            "Sadrul Habib Chowdhury", "Martijn Voncken"])
        self.about.set_artists(["Andrew Wedderburn", "Andrew Resch"])
        self.about.set_translator_credits(_("translator-credits"))
        self.about.set_license(_("Deluge is free software, you can redistribute \
it and/or\nmodify it under the terms of the GNU General Public\n License as \
published by the Free Software Foundation,\neither version 2 of the License, \
or (at your option) any\nlater version.  Deluge is distributed in the hope \
that it\nwill be useful, but WITHOUT ANY WARRANTY, without even \nthe implied \
warranty of MERCHANTABILITY or FITNESS\nFOR A PARTICULAR PURPOSE.  See the GNU \
General\nPublic License for more details.  You should have received\na copy of \
the GNU General Public License along with\nDeluge, but if not, write to the \
Free Software Foundation,\n Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110\
-\n1301 USA"))
        self.about.set_website("http://deluge-torrent.org")
        self.about.set_website_label("http://deluge-torrent.org")
        self.about.set_icon(deluge.common.get_logo(32))
        self.about.set_logo(gtk.gdk.pixbuf_new_from_file(
                                deluge.common.get_pixmap("deluge-about.png")))
      
    def run(self):
        self.about.show_all()
        self.about.run()
        self.about.destroy()
