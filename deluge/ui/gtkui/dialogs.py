#
# dialogs.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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
# 	Boston, MA  02110-1301, USA.
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
#

import gtk
import deluge.component as component

class YesNoDialog(gtk.Dialog):
    """
    Displays a dialog asking the user to select Yes or No to a question.

    When run(), it will return either a gtk.RESPONSE_YES or a gtk.RESPONSE_NO.

    """
    def __init__(self, header, text, parent=None):
        """
        :param header: str, the header portion of the dialog, try to keep it short and to the point
        :param text: str, the body of the dialog, this can be longer with a more
            thorough explanation of the question
        :param parent: gtkWindow, the parent window, if None it will default to the
            MainWindow
        """
        super(YesNoDialog, self).__init__(
            title="",
            parent=parent if parent else component.get("MainWindow").window,
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
            buttons=(gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO, gtk.RESPONSE_NO))

        # XXX: All of this stuff should be moved to a base dialog class..
        self.set_border_width(5)
        self.set_default_size(200, 100)
        hbox = gtk.HBox(spacing=5)
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
        image.set_alignment(0.5, 0.0)
        hbox.pack_start(image, False, False)
        vbox = gtk.VBox(spacing=5)
        label = gtk.Label("<b><big>" + header + "</big></b>")
        label.set_use_markup(True)
        label.set_alignment(0.0, 0.5)
        label.set_line_wrap(True)
        vbox.pack_start(label, False, False)
        tlabel = gtk.Label(text)
        tlabel.set_use_markup(True)
        tlabel.set_line_wrap(True)
        tlabel.set_alignment(0.0, 0.5)
        vbox.pack_start(tlabel, False, False)
        hbox.pack_start(vbox, False, False)
        self.vbox.pack_start(hbox, False, False)
        self.vbox.show_all()

    def run(self):
        response = super(YesNoDialog, self).run()
        self.destroy()
        return response
