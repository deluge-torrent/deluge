#
# gtkui.py
#
# Copyright (C) 2009 Pedro Algarvio <ufs@ufsoft.org>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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
from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

try:
    import pygame
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

try:
    import pynotify
    POPUP_ENABLED = True
except ImportError:
    POPUP_ENABLED = False

# Relative imports
from common import get_resource
from manager import Notifications

RECIPIENT_FIELD, RECIPIENT_EDIT = range(2)

class GtkUI(GtkPluginBase, Notifications):
    def enable(self):
        Notifications.enable(self)
        self.glade = gtk.glade.XML(get_resource("config.glade"))
        self.glade.get_widget("smtp_port").set_value(25)
        self.prefs = self.glade.get_widget("prefs_box")
        self.prefs.show_all()
        self.treeview = self.glade.get_widget("smtp_recipients")
        treeview_selection = self.treeview.get_selection()
        treeview_selection.connect("changed", self.on_treeview_selection_changed)
        self.model = gtk.ListStore(str, bool)

        renderer = gtk.CellRendererText()
        renderer.connect("edited", self.on_cell_edited, self.model)
        renderer.set_data("recipient", RECIPIENT_FIELD)
        column = gtk.TreeViewColumn("Recipients", renderer,
                                    text=RECIPIENT_FIELD,
                                    editable=RECIPIENT_EDIT)
        column.set_expand(True)
        self.treeview.append_column(column)
        self.treeview.set_model(self.model)

        deluge.common.get_default_download_dir()

        self.glade.signal_autoconnect({
            'on_add_button_clicked': (self.on_add_button_clicked,
                                      self.treeview),
            'on_delete_button_clicked': (self.on_delete_button_clicked,
                                         self.treeview),
            'on_enabled_toggled': self.on_enabled_toggled,
            'on_sound_enabled_toggled': self.on_sound_enabled_toggled
        })

        component.get("Preferences").add_page("Notifications", self.prefs)
        component.get("PluginManager").register_hook("on_apply_prefs",
                                                     self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs",
                                                     self.on_show_prefs)

        if not POPUP_ENABLED:
            self.glade.get_widget("popup_enabled").set_property('sensitive',
                                                                False)
        else:
            client.register_event_handler("NotificationPopupEvent",
                                          self.notify_popup)

        client.register_event_handler("NotificationBlinkEvent",
                                      self.notify_blink)

        self.tray = component.get("SystemTray")
        if not SOUND_AVAILABLE:
            self.glade.get_widget("sound_enabled").set_property('sensitive',
                                                                False)
            self.glade.get_widget('sound_path').set_property('sensitive', False)
        else:
            client.register_event_handler("NotificationSoundEvent",
                                          self.notify_sound)
        # Force config populate
        client.notifications.get_config().addCallback(self.cb_get_config)

    def disable(self):
        Notifications.disable(self)
        component.get("Preferences").remove_page("Notifications")
        component.get("PluginManager").deregister_hook("on_apply_prefs",
                                                       self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs",
                                                       self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for Notifications")
        config = {
            "smtp_enabled": self.glade.get_widget("smtp_enabled").get_active(),
            "smtp_host": self.glade.get_widget("smtp_host").get_text(),
            "smtp_port": self.glade.get_widget("smtp_port").get_value(),
            "smtp_user": self.glade.get_widget("smtp_user").get_text(),
            "smtp_pass": self.glade.get_widget("smtp_pass").get_text(),
            "smtp_from": self.glade.get_widget("smtp_from").get_text(),
            "smtp_tls": self.glade.get_widget("smtp_tls").get_active(),
            "smtp_recipients": [dest[0] for dest in self.model if
                                dest[0]!='USER@HOST'],
            "blink_enabled": self.glade.get_widget("blink_enabled").get_active(),
            "sound_enabled": self.glade.get_widget("sound_enabled").get_active(),
            "sound_path": self.glade.get_widget("sound_path").get_filename(),
            "popup_enabled": self.glade.get_widget("popup_enabled").get_active()
        }

        client.notifications.set_config(config)

    def on_show_prefs(self):
        client.notifications.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.config = config
        self.glade.get_widget("smtp_host").set_text(config["smtp_host"])
        self.glade.get_widget("smtp_port").set_value(config["smtp_port"])
        self.glade.get_widget("smtp_user").set_text(config["smtp_user"])
        self.glade.get_widget("smtp_pass").set_text(config["smtp_pass"])
        self.glade.get_widget("smtp_from").set_text(config["smtp_from"])
        self.glade.get_widget("smtp_tls").set_active(config["smtp_tls"])
        self.model.clear()
        for recipient in config['smtp_recipients']:
            self.model.set(self.model.append(),
                           RECIPIENT_FIELD, recipient,
                           RECIPIENT_EDIT, False)
        self.glade.get_widget("smtp_enabled").set_active(config['smtp_enabled'])
        self.glade.get_widget("sound_enabled").set_active(
            config['sound_enabled']
        )
        self.glade.get_widget("popup_enabled").set_active(
            config['popup_enabled']
        )
        self.glade.get_widget("blink_enabled").set_active(
            config['blink_enabled']
        )
        if config['sound_path']:
            sound_path = config['sound_path']
        else:
            sound_path = deluge.common.get_default_download_dir()
        self.glade.get_widget("sound_path").set_filename(sound_path)
        # Force toggle
        self.on_enabled_toggled(self.glade.get_widget("smtp_enabled"))
        self.on_sound_enabled_toggled(self.glade.get_widget('sound_enabled'))

    def on_add_button_clicked(self, widget, treeview):
        model = treeview.get_model()
        model.set(model.append(),
                  RECIPIENT_FIELD, "USER@HOST",
                  RECIPIENT_EDIT, True)

    def on_delete_button_clicked(self, widget, treeview):
        selection = treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            path = model.get_path(iter)[0]
            model.remove(iter)

    def on_cell_edited(self, cell, path_string, new_text, model):
        log.debug("%s %s %s %s", cell, path_string, new_text, model)
        iter = model.get_iter_from_string(path_string)
        path = model.get_path(iter)[0]
        model.set(iter, RECIPIENT_FIELD, new_text)

    def on_treeview_selection_changed(self, selection):
        model, selected_connection_iter = selection.get_selected()
        if selected_connection_iter:
            self.glade.get_widget("delete_button").set_property('sensitive',
                                                                True)
        else:
            self.glade.get_widget("delete_button").set_property('sensitive',
                                                                False)
    def on_enabled_toggled(self, widget):
        if widget.get_active():
            for widget in ('smtp_host', 'smtp_port', 'smtp_user', 'smtp_pass',
                           'smtp_pass', 'smtp_tls', 'smtp_from',
                           'smtp_recipients'):
                self.glade.get_widget(widget).set_property('sensitive', True)
        else:
            for widget in ('smtp_host', 'smtp_port', 'smtp_user', 'smtp_pass',
                           'smtp_pass', 'smtp_tls', 'smtp_from',
                           'smtp_recipients'):
                self.glade.get_widget(widget).set_property('sensitive', False)


    def on_sound_enabled_toggled(self, widget):
        if widget.get_active():
            self.glade.get_widget('sound_path').set_property('sensitive', True)
        else:
            self.glade.get_widget('sound_path').set_property('sensitive', False)

    def notify_blink(self):
        return defer.maybeDeferred(self.tray.blink, True)

    def notify_email(self, title='', message='', smtp_from='', recipients=[]):
        client.notifications.notify_email(title, message, smtp_from, recipients)

    def notify_flash(self, title='', message=''):
        client.notifications.notify_flash(title, message)

    def notify_popup(self, title='', message=''):
        if not self.config['popup_enabled']:
            return defer.succeed("Popup notification is not enabled.")
        if not POPUP_ENABLED:
            return defer.fail("pynotify is not installed")

        if pynotify.init("Deluge"):
            icon = gtk.gdk.pixbuf_new_from_file_at_size(
                            deluge.common.get_pixmap("deluge.svg"), 48, 48)
            self.note = pynotify.Notification(title, message)
            self.note.set_icon_from_pixbuf(icon)
            if not self.note.show():
                log.warning("pynotify failed to show notification")
                return defer.fail("pynotify failed to show notification")
        return defer.succeed("Notification popup shown")

    def notify_sound(self, sound_path=''):
        if not self.config['sound_enabled']:
            return defer.succeed("Sound notification not enabled")
        if not SOUND_AVAILABLE:
            log.warning("pygame is not installed")
            return defer.fail("pygame is not installed")

        pygame.init()
        try:
            if not sound_path:
                sound_path = self.config['sound_path']
            alert_sound = pygame.mixer.music
            alert_sound.load(sound_path)
            alert_sound.play()
        except pygame.error, message:
            log.warning("pygame failed to play because %s" % (message))
            return defer.fail("Sound notification failed %s" % (message))
        else:
            log.info("sound notification played successfully")
            return defer.succeed("Sound notification Success")

