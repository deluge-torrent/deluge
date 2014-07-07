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

from twisted.internet import defer

import deluge.component as component


class BaseDialog(gtk.Dialog):
    """
    Base dialog class that should be used with all dialogs.
    """
    def __init__(self, header, text, icon, buttons, parent=None):
        """
        :param header: str, the header portion of the dialog
        :param text: str, the text body of the dialog
        :param icon: gtk Stock ID, a stock id for the gtk icon to display
        :param buttons: tuple, of gtk stock ids and responses
        :param parent: gtkWindow, the parent window, if None it will default to the
            MainWindow
        """
        super(BaseDialog, self).__init__(
            title="",
            parent=parent if parent else component.get("MainWindow").window,
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
            buttons=buttons)

        self.connect("delete-event", self._on_delete_event)
        self.connect("response", self._on_response)

        # Setup all the formatting and such to make our dialog look pretty
        self.set_border_width(5)
        self.set_default_size(200, 100)
        hbox = gtk.HBox(spacing=5)
        image = gtk.Image()
        image.set_from_stock(icon, gtk.ICON_SIZE_DIALOG)
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
        self.vbox.set_spacing(5)
        self.vbox.show_all()

    def _on_delete_event(self, widget, event):
        self.deferred.callback(gtk.RESPONSE_DELETE_EVENT)
        self.destroy()

    def _on_response(self, widget, response):
        self.deferred.callback(response)
        self.destroy()

    def run(self):
        """
        Shows the dialog and returns a Deferred object.  The deferred, when fired
        will contain the response ID.
        """
        self.deferred = defer.Deferred()
        self.show()
        return self.deferred

class YesNoDialog(BaseDialog):
    """
    Displays a dialog asking the user to select Yes or No to a question.

    When run(), it will return either a gtk.RESPONSE_YES or a gtk.RESPONSE_NO.

    """
    def __init__(self, header, text, parent=None):
        """
        :param header: see `:class:BaseDialog`
        :param text: see `:class:BaseDialog`
        :param parent: see `:class:BaseDialog`
        """
        super(YesNoDialog, self).__init__(
            header,
            text,
            gtk.STOCK_DIALOG_QUESTION,
            (gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO, gtk.RESPONSE_NO),
            parent)

class InformationDialog(BaseDialog):
    """
    Displays an information dialog.

    When run(), it will return a gtk.RESPONSE_CLOSE.
    """
    def __init__(self, header, text, parent=None):
        """
        :param header: see `:class:BaseDialog`
        :param text: see `:class:BaseDialog`
        :param parent: see `:class:BaseDialog`
        """
        super(InformationDialog, self).__init__(
            header,
            text,
            gtk.STOCK_DIALOG_INFO,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE),
            parent)

class ErrorDialog(BaseDialog):
    """
    Displays an error dialog with optional details text for more information.

    When run(), it will return a gtk.RESPONSE_CLOSE.
    """
    def __init__(self, header, text, parent=None, details=None):
        """
        :param header: see `:class:BaseDialog`
        :param text: see `:class:BaseDialog`
        :param parent: see `:class:BaseDialog`
        :param details: str, extra information that will be displayed in a
            scrollable textview
        """
        super(ErrorDialog, self).__init__(
            header,
            text,
            gtk.STOCK_DIALOG_ERROR,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE),
            parent)

        if details:
            self.set_default_size(500, 400)
            textview = gtk.TextView()
            textview.set_editable(False)
            textview.get_buffer().set_text(details)
            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            sw.set_shadow_type(gtk.SHADOW_IN)
            sw.add(textview)
            label = gtk.Label(_("Details:"))
            label.set_alignment(0.0, 0.5)
            self.vbox.pack_start(label, False, False)
            self.vbox.pack_start(sw)
            self.vbox.show_all()

class PasswordDialog(BaseDialog):
    """
    Displays a dialog with an entry field asking for a password.

    When run(), it will return either a gtk.RESPONSE_CANCEL or a gtk.RESPONSE_OK.
    """
    def __init__(self, password_msg="", parent=None):
        """
        :param password_msg: the error message we got back from the server
        :type password_msg: string
        """
        super(PasswordDialog, self).__init__(
            _("Password Protected"), password_msg,
            gtk.STOCK_DIALOG_AUTHENTICATION,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_CONNECT, gtk.RESPONSE_OK),
            parent)

        table = gtk.Table(1, 2, False)
        self.password_label = gtk.Label()
        self.password_label.set_markup("<b>" + _("Password:") + "</b>")
        self.password_label.set_alignment(1.0, 0.5)
        self.password_label.set_padding(5, 5)
        self.password_entry = gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.connect("activate", self.on_password_activate)
        table.attach(self.password_label, 0, 1, 1, 2)
        table.attach(self.password_entry, 1, 2, 1, 2)

        self.vbox.pack_start(table, False, False, padding=5)
        self.set_focus(self.password_entry)
        self.show_all()

    def get_password(self):
        return self.password_entry.get_text()

    def on_password_activate(self, widget):
        self.response(gtk.RESPONSE_OK)
