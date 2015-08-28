# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from gi.repository import GdkPixbuf, Gtk
from twisted.internet import defer

import deluge.component as component
from deluge.common import get_pixmap, osx_check, windows_check
from deluge.ui.gtkui.common import get_deluge_icon


class BaseDialog(Gtk.Dialog):
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
            title=header,
            parent=parent if parent else component.get("MainWindow").window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            buttons=buttons)

        self.set_icon(get_deluge_icon())

        self.connect("delete-event", self._on_delete_event)
        self.connect("response", self._on_response)

        # Setup all the formatting and such to make our dialog look pretty
        self.set_border_width(5)
        self.set_default_size(200, 100)
        hbox = Gtk.HBox(spacing=5)
        image = Gtk.Image()
        if not Gtk.stock_lookup(icon) and (icon.endswith(".svg") or icon.endswith(".png")):
            # Hack for Windows since it doesn't support svg
            if icon.endswith(".svg") and (windows_check() or osx_check()):
                icon = icon.rpartition(".svg")[0] + "16.png"
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(get_pixmap(icon), 32, 32)
            image.set_from_pixbuf(pixbuf)
        else:
            image.set_from_stock(icon, Gtk.IconSize.DIALOG)
        image.set_alignment(0.5, 0.0)
        hbox.pack_start(image, False, False, 0)
        vbox = Gtk.VBox(spacing=5)
        tlabel = Gtk.Label(label=text)
        tlabel.set_use_markup(True)
        tlabel.set_line_wrap(True)
        tlabel.set_alignment(0.0, 0.5)
        vbox.pack_start(tlabel, False, False, 0)
        hbox.pack_start(vbox, False, False, 0)
        self.vbox.pack_start(hbox, False, False, 0)
        self.vbox.set_spacing(5)
        self.vbox.show_all()

    def _on_delete_event(self, widget, event):
        self.deferred.callback(Gtk.ResponseType.DELETE_EVENT)
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

    When run(), it will return either a Gtk.ResponseType.YES or a Gtk.ResponseType.NO.

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
            Gtk.STOCK_DIALOG_QUESTION,
            (Gtk.STOCK_NO, Gtk.ResponseType.NO, Gtk.STOCK_YES, Gtk.ResponseType.YES),
            parent)


class InformationDialog(BaseDialog):
    """
    Displays an information dialog.

    When run(), it will return a Gtk.ResponseType.CLOSE.
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
            Gtk.STOCK_DIALOG_INFO,
            (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE),
            parent)


class ErrorDialog(BaseDialog):
    """
    Displays an error dialog with optional details text for more information.

    When run(), it will return a Gtk.ResponseType.CLOSE.
    """
    def __init__(self, header, text, parent=None, details=None, traceback=False):
        """
        :param header: see `:class:BaseDialog`
        :param text: see `:class:BaseDialog`
        :param parent: see `:class:BaseDialog`
        :param details: extra information that will be displayed in a
            scrollable textview
        :type details: string
        :param traceback: show the traceback information in the details area
        :type traceback: bool
        """
        super(ErrorDialog, self).__init__(
            header,
            text,
            Gtk.STOCK_DIALOG_ERROR,
            (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE),
            parent)

        if traceback:
            import traceback
            import sys
            tb = sys.exc_info()
            tb = traceback.format_exc(tb[2])
            if details:
                details += "\n" + tb
            else:
                details = tb

        if details:
            self.set_default_size(600, 400)
            textview = Gtk.TextView()
            textview.set_editable(False)
            textview.get_buffer().set_text(details)
            sw = Gtk.ScrolledWindow()
            sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            sw.set_shadow_type(Gtk.ShadowType.IN)
            sw.add(textview)
            label = Gtk.Label(label=_("Details:"))
            label.set_alignment(0.0, 0.5)
            self.vbox.pack_start(label, False, False, 0)
            self.vbox.pack_start(sw, True, True, 0)
            self.vbox.show_all()


class AuthenticationDialog(BaseDialog):
    """
    Displays a dialog with entry fields asking for username and password.

    When run(), it will return either a Gtk.ResponseType.CANCEL or a
    Gtk.ResponseType.OK.
    """
    def __init__(self, err_msg="", username=None, parent=None):
        """
        :param err_msg: the error message we got back from the server
        :type err_msg: string
        """
        super(AuthenticationDialog, self).__init__(
            _("Authenticate"), err_msg,
            Gtk.STOCK_DIALOG_AUTHENTICATION,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_CONNECT, Gtk.ResponseType.OK),
            parent)

        table = Gtk.Table(2, 2, False)
        self.username_label = Gtk.Label()
        self.username_label.set_markup("<b>" + _("Username:") + "</b>")
        self.username_label.set_alignment(1.0, 0.5)
        self.username_label.set_padding(5, 5)
        self.username_entry = Gtk.Entry()
        table.attach(self.username_label, 0, 1, 0, 1)
        table.attach(self.username_entry, 1, 2, 0, 1)

        self.password_label = Gtk.Label()
        self.password_label.set_markup("<b>" + _("Password:") + "</b>")
        self.password_label.set_alignment(1.0, 0.5)
        self.password_label.set_padding(5, 5)
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.connect("activate", self.on_password_activate)
        table.attach(self.password_label, 0, 1, 1, 2)
        table.attach(self.password_entry, 1, 2, 1, 2)

        self.vbox.pack_start(table, False, False, padding=5)
        self.set_focus(self.password_entry)
        if username:
            self.username_entry.set_text(username)
            self.username_entry.set_editable(False)
            self.set_focus(self.password_entry)
        else:
            self.set_focus(self.username_entry)
        self.show_all()

    def get_username(self):
        return self.username_entry.get_text()

    def get_password(self):
        return self.password_entry.get_text()

    def on_password_activate(self, widget):
        self.response(Gtk.ResponseType.OK)


class AccountDialog(BaseDialog):
    def __init__(self, username=None, password=None, authlevel=None,
                 levels_mapping=None, parent=None):
        if username:
            super(AccountDialog, self).__init__(
                _("Edit Account"),
                _("Edit existing account"),
                Gtk.STOCK_DIALOG_INFO,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                 Gtk.STOCK_APPLY, Gtk.ResponseType.OK),
                parent)
        else:
            super(AccountDialog, self).__init__(
                _("New Account"),
                _("Create a new account"),
                Gtk.STOCK_DIALOG_INFO,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                 Gtk.STOCK_ADD, Gtk.ResponseType.OK),
                parent)

        self.levels_mapping = levels_mapping

        table = Gtk.Table(2, 3, False)
        self.username_label = Gtk.Label()
        self.username_label.set_markup("<b>" + _("Username:") + "</b>")
        self.username_label.set_alignment(1.0, 0.5)
        self.username_label.set_padding(5, 5)
        self.username_entry = Gtk.Entry()
        table.attach(self.username_label, 0, 1, 0, 1)
        table.attach(self.username_entry, 1, 2, 0, 1)

        self.authlevel_label = Gtk.Label()
        self.authlevel_label.set_markup("<b>" + _("Authentication Level:") + "</b>")
        self.authlevel_label.set_alignment(1.0, 0.5)
        self.authlevel_label.set_padding(5, 5)

        self.authlevel_combo = Gtk.ComboBoxText()
        active_idx = None
        for idx, level in enumerate(levels_mapping.keys()):
            self.authlevel_combo.append_text(level)
            if authlevel and authlevel == level:
                active_idx = idx
            elif not authlevel and level == 'DEFAULT':
                active_idx = idx

        if active_idx is not None:
            self.authlevel_combo.set_active(active_idx)

        table.attach(self.authlevel_label, 0, 1, 1, 2)
        table.attach(self.authlevel_combo, 1, 2, 1, 2)

        self.password_label = Gtk.Label()
        self.password_label.set_markup("<b>" + _("Password:") + "</b>")
        self.password_label.set_alignment(1.0, 0.5)
        self.password_label.set_padding(5, 5)
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        table.attach(self.password_label, 0, 1, 2, 3)
        table.attach(self.password_entry, 1, 2, 2, 3)

        self.vbox.pack_start(table, False, False, padding=5)
        if username:
            self.username_entry.set_text(username)
            self.username_entry.set_editable(False)
        else:
            self.set_focus(self.username_entry)

        if password:
            self.password_entry.set_text(username)

        self.show_all()

    def get_username(self):
        return self.username_entry.get_text()

    def get_password(self):
        return self.password_entry.get_text()

    def get_authlevel(self):
        combobox = self.authlevel_combo
        level = combobox.get_model()[combobox.get_active()][0]
        return level


class OtherDialog(BaseDialog):
    """
    Displays a dialog with a spinner for setting a value.

    Returns:
        int or float:
    """
    def __init__(self, header, text="", unit_text="", icon=None, default=0, parent=None):
        self.value_type = type(default)
        if self.value_type not in (int, float):
            raise TypeError("default value needs to be an int or float")

        if not icon:
            icon = Gtk.STOCK_DIALOG_INFO

        super(OtherDialog, self).__init__(
            header,
            text,
            icon,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_APPLY, Gtk.ResponseType.OK),
            parent)

        hbox = Gtk.HBox(spacing=5)
        alignment_spacer = Gtk.Alignment.new(0, 0, 0, 0)
        hbox.pack_start(alignment_spacer, True, True, 0)
        alignment_spin = Gtk.Alignment.new(1, 0.5, 1, 1)
        adjustment_spin = Gtk.Adjustment.new(50.0, -1.0, 100000.0, 1.0, 10.0, 0.0)
        self.spinbutton = Gtk.SpinButton.new(adjustment_spin, 0, 0)
        self.spinbutton.set_value(default)
        self.spinbutton.select_region(0, -1)
        self.spinbutton.set_width_chars(6)
        self.spinbutton.set_alignment(1)
        self.spinbutton.set_max_length(6)
        if self.value_type is float:
            self.spinbutton.set_digits(1)
        alignment_spin.add(self.spinbutton)
        hbox.pack_start(alignment_spin, False, True, 0)
        label_type = Gtk.Label()
        label_type.set_text(unit_text)
        label_type.set_alignment(0.0, 0.5)
        hbox.pack_start(label_type, True, True, 0)

        self.vbox.pack_start(hbox, False, False, padding=5)
        self.vbox.show_all()

    def _on_delete_event(self, widget, event):
        self.deferred.callback(None)
        self.destroy()

    def _on_response(self, widget, response):
        value = None
        if response == Gtk.ResponseType.OK:
            if self.value_type is int:
                value = self.spinbutton.get_value_as_int()
            else:
                value = self.spinbutton.get_value()
        self.deferred.callback(value)
        self.destroy()


class PasswordDialog(BaseDialog):
    """
    Displays a dialog with an entry field asking for a password.

    When run(), it will return either a Gtk.ResponseType.CANCEL or a Gtk.ResponseType.OK.
    """
    def __init__(self, password_msg="", parent=None):
        """
        :param password_msg: the error message we got back from the server
        :type password_msg: string
        """
        super(PasswordDialog, self).__init__(
            _("Password Protected"), password_msg,
            Gtk.STOCK_DIALOG_AUTHENTICATION,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_CONNECT, Gtk.ResponseType.OK),
            parent)

        table = Gtk.Table(1, 2, False)
        self.password_label = Gtk.Label()
        self.password_label.set_markup("<b>" + _("Password:") + "</b>")
        self.password_label.set_alignment(1.0, 0.5)
        self.password_label.set_padding(5, 5)
        self.password_entry = Gtk.Entry()
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
        self.response(Gtk.ResponseType.OK)
