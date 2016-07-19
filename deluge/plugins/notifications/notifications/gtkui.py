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

from os.path import basename
import gtk

from twisted.internet import defer
from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common
import deluge.configmanager

# Relative imports
from common import get_resource, CustomNotifications

try:
    import pygame
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

try:
    import pynotify
    POPUP_AVAILABLE = True
    if deluge.common.windows_check():
        POPUP_AVAILABLE = False
except ImportError:
    POPUP_AVAILABLE = False


DEFAULT_PREFS = {
    # BLINK
    "blink_enabled": False,
    # FLASH
    "flash_enabled": False,
    # POPUP
    "popup_enabled": False,
    # SOUND
    "sound_enabled": False,
    "sound_path": "",
    "custom_sounds": {},
    # Subscriptions
    "subscriptions": {
        "popup": [],
        "blink": [],
        "sound": [],
    },
}

RECIPIENT_FIELD, RECIPIENT_EDIT = range(2)
(SUB_EVENT, SUB_EVENT_DOC, SUB_NOT_EMAIL, SUB_NOT_POPUP, SUB_NOT_BLINK,
 SUB_NOT_SOUND) = range(6)
SND_EVENT, SND_EVENT_DOC, SND_NAME, SND_PATH = range(4)

class GtkUiNotifications(CustomNotifications):

    def enable(self):
        CustomNotifications.enable(self)
        self.register_custom_blink_notification(
            "TorrentFinishedEvent", self._on_torrent_finished_event_blink
        )
        self.register_custom_sound_notification(
            "TorrentFinishedEvent", self._on_torrent_finished_event_sound
        )
        self.register_custom_popup_notification(
            "TorrentFinishedEvent", self._on_torrent_finished_event_popup
        )

    def disable(self):
        self.deregister_custom_blink_notification("TorrentFinishedEvent")
        self.deregister_custom_sound_notification("TorrentFinishedEvent")
        self.deregister_custom_popup_notification("TorrentFinishedEvent")
        CustomNotifications.disable(self)

    def register_custom_popup_notification(self, eventtype, handler):
        """This is used to register popup notifications for custom event types.

        :param event: the event name
        :param type: string
        :param handler: function, to be called when `:param:event` is emitted

        Your handler should return a tuple of (popup_title, popup_contents).
        """
        self._register_custom_provider('popup', eventtype, handler)

    def deregister_custom_popup_notification(self, eventtype):
        self._deregister_custom_provider('popup', eventtype)

    def register_custom_blink_notification(self, eventtype, handler):
        """This is used to register blink notifications for custom event types.

        :param event: str, the event name
        :param handler: function, to be called when `:param:event` is emitted

        Your handler should return `True` or `False` to blink or not the
        trayicon.
        """
        self._register_custom_provider('blink', eventtype, handler)

    def deregister_custom_blink_notification(self, eventtype):
        self._deregister_custom_provider('blink', eventtype)

    def register_custom_sound_notification(self, eventtype, handler):
        """This is used to register sound notifications for custom event types.

        :param event: the event name
        :type event: string
        :param handler: function to be called when `:param:event` is emitted

        Your handler should return either '' to use the sound defined on the
        notification preferences, the path to a sound file, which will then be
        played or None, where no sound will be played at all.
        """
        self._register_custom_provider('sound', eventtype, handler)

    def deregister_custom_sound_notification(self, eventtype):
        self._deregister_custom_provider('sound', eventtype)

    def handle_custom_popup_notification(self, result, eventtype):
        title, message = result
        return defer.maybeDeferred(self.__popup, title, message)

    def handle_custom_blink_notification(self, result, eventtype):
        if result:
            return defer.maybeDeferred(self.__blink)
        return defer.succeed("Won't blink. The returned value from the custom "
                             "handler was: %s", result)

    def handle_custom_sound_notification(self, result, eventtype):
        if isinstance(result, basestring):
            if not result and eventtype in self.config['custom_sounds']:
                return defer.maybeDeferred(
                    self.__play_sound, self.config['custom_sounds'][eventtype])
            return defer.maybeDeferred(self.__play_sound, result)
        return defer.succeed("Won't play sound. The returned value from the "
                             "custom handler was: %s", result)

    def __blink(self):
        self.systray.blink(True)
        return defer.succeed(_("Notification Blink shown"))

    def __popup(self, title='', message=''):
        import gtk
        if not self.config['popup_enabled']:
            return defer.succeed(_("Popup notification is not enabled."))
        if not POPUP_AVAILABLE:
            return defer.fail(_("pynotify is not installed"))

        if pynotify.init("Deluge"):
            icon = gtk.gdk.pixbuf_new_from_file_at_size(
                            deluge.common.get_pixmap("deluge.svg"), 48, 48)
            self.note = pynotify.Notification(title, message)
            self.note.set_icon_from_pixbuf(icon)
            if not self.note.show():
                err_msg = _("pynotify failed to show notification")
                log.warning(err_msg)
                return defer.fail(err_msg)
        return defer.succeed(_("Notification popup shown"))

    def __play_sound(self, sound_path=''):
        if not self.config['sound_enabled']:
            return defer.succeed(_("Sound notification not enabled"))
        if not SOUND_AVAILABLE:
            err_msg = _("pygame is not installed")
            log.warning(err_msg)
            return defer.fail(err_msg)

        pygame.init()
        try:
            if not sound_path:
                sound_path = self.config['sound_path']
            alert_sound = pygame.mixer.music
            alert_sound.load(sound_path)
            alert_sound.play()
        except pygame.error, message:
            err_msg = _("Sound notification failed %s") % (message)
            log.warning(err_msg)
            return defer.fail(err_msg)
        else:
            msg = _("Sound notification Success")
            log.info(msg)
            return defer.succeed(msg)

    def _on_torrent_finished_event_blink(self, torrent_id):
        return True # Yes, Blink

    def _on_torrent_finished_event_sound(self, torrent_id):
        # Since there's no custom sound hardcoded, just return ''
        return ''

    def _on_torrent_finished_event_popup(self, torrent_id):
        d = client.core.get_torrent_status(torrent_id, ["name", "file_progress"])
        d.addCallback(self._on_torrent_finished_event_got_torrent_status)
        d.addErrback(self._on_torrent_finished_event_torrent_status_failure)
        return d

    def _on_torrent_finished_event_torrent_status_failure(self, failure):
        log.debug("Failed to get torrent status to be able to show the popup")

    def _on_torrent_finished_event_got_torrent_status(self, torrent_status):
        log.debug("Handler for TorrentFinishedEvent GTKUI called. "
                  "Got Torrent Status")
        title = _("Finished Torrent")
        torrent_status["num_files"] = torrent_status["file_progress"].count(1.0)
        message = _("The torrent \"%(name)s\" including %(num_files)i file(s) "
                    "has finished downloading.") % torrent_status
        return title, message

class GtkUI(GtkPluginBase, GtkUiNotifications):
    def __init__(self, plugin_name):
        GtkPluginBase.__init__(self, plugin_name)
        GtkUiNotifications.__init__(self)

    def enable(self):
        self.config = deluge.configmanager.ConfigManager(
            "notifications-gtk.conf", DEFAULT_PREFS
        )
        self.glade = gtk.glade.XML(get_resource("config.glade"))
        self.prefs = self.glade.get_widget("prefs_box")
        self.prefs.show_all()

        self.build_recipients_model_populate_treeview()
        self.build_sounds_model_populate_treeview()
        self.build_notifications_model_populate_treeview()


        client.notifications.get_handled_events().addCallback(
            self.popuplate_what_needs_handled_events
        )

        self.glade.signal_autoconnect({
            'on_add_button_clicked': (self.on_add_button_clicked,
                                      self.recipients_treeview),
            'on_delete_button_clicked': (self.on_delete_button_clicked,
                                         self.recipients_treeview),
            'on_enabled_toggled': self.on_enabled_toggled,
            'on_sound_enabled_toggled': self.on_sound_enabled_toggled,
            'on_sounds_edit_button_clicked': self.on_sounds_edit_button_clicked,
            'on_sounds_revert_button_clicked': \
                                        self.on_sounds_revert_button_clicked,
            'on_sound_path_update_preview': self.on_sound_path_update_preview
        })

        prefs = component.get("Preferences")
        parent = self.prefs.get_parent()
        if parent:
            parent.remove(self.prefs)
        index = prefs.notebook.append_page(self.prefs)
        prefs.liststore.append([index, _("Notifications")])

        component.get("PluginManager").register_hook("on_apply_prefs",
                                                     self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs",
                                                     self.on_show_prefs)

        if not POPUP_AVAILABLE:
            self.glade.get_widget("popup_enabled").set_property('sensitive',
                                                                False)
        if not SOUND_AVAILABLE:
#            for widget_name in ('sound_enabled', 'sound_path', 'sounds_page',
#                                'sounds_page_label'):
#                self.glade.get_widget(widget_name).set_property('sensitive',
#                                                                False)
            self.glade.get_widget("sound_enabled").set_property('sensitive',
                                                                False)
            self.glade.get_widget('sound_path').set_property('sensitive', False)
            self.glade.get_widget('sounds_page').set_property('sensitive',
                                                              False)
            self.glade.get_widget('sounds_page_label').set_property('sensitive',
                                                                    False)

        self.systray = component.get("SystemTray")
        if not hasattr(self.systray, 'tray'):
            # Tray is not beeing used
            self.glade.get_widget('blink_enabled').set_property('sensitive',
                                                                False)

        GtkUiNotifications.enable(self)

    def disable(self):
        GtkUiNotifications.disable(self)
        component.get("Preferences").remove_page(_("Notifications"))
        component.get("PluginManager").deregister_hook("on_apply_prefs",
                                                       self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs",
                                                       self.on_show_prefs)

    def build_recipients_model_populate_treeview(self):
        # SMTP Recipients treeview/model
        self.recipients_treeview = self.glade.get_widget("smtp_recipients")
        treeview_selection = self.recipients_treeview.get_selection()
        treeview_selection.connect(
            "changed", self.on_recipients_treeview_selection_changed
        )
        self.recipients_model = gtk.ListStore(str, bool)

        renderer = gtk.CellRendererText()
        renderer.connect("edited", self.on_cell_edited, self.recipients_model)
        renderer.set_data("recipient", RECIPIENT_FIELD)
        column = gtk.TreeViewColumn("Recipients", renderer,
                                    text=RECIPIENT_FIELD,
                                    editable=RECIPIENT_EDIT)
        column.set_expand(True)
        self.recipients_treeview.append_column(column)
        self.recipients_treeview.set_model(self.recipients_model)

    def build_sounds_model_populate_treeview(self):
        # Sound customisation treeview/model
        self.sounds_treeview = self.glade.get_widget('sounds_treeview')
        sounds_selection = self.sounds_treeview.get_selection()
        sounds_selection.connect(
            "changed", self.on_sounds_treeview_selection_changed
        )

        self.sounds_treeview.set_tooltip_column(SND_EVENT_DOC)
        self.sounds_model = gtk.ListStore(str, str, str, str)

        renderer = gtk.CellRendererText()
        renderer.set_data("event", SND_EVENT)
        column = gtk.TreeViewColumn("Event", renderer, text=SND_EVENT)
        column.set_expand(True)
        self.sounds_treeview.append_column(column)

        renderer = gtk.CellRendererText()
        renderer.set_data("event_doc", SND_EVENT_DOC)
        column = gtk.TreeViewColumn("Doc", renderer, text=SND_EVENT_DOC)
        column.set_property('visible', False)
        self.sounds_treeview.append_column(column)

        renderer = gtk.CellRendererText()
        renderer.set_data("sound_name", SND_NAME)
        column = gtk.TreeViewColumn("Name", renderer, text=SND_NAME)
        self.sounds_treeview.append_column(column)

        renderer = gtk.CellRendererText()
        renderer.set_data("sound_path", SND_PATH)
        column = gtk.TreeViewColumn("Path", renderer, text=SND_PATH)
        column.set_property('visible', False)
        self.sounds_treeview.append_column(column)

        self.sounds_treeview.set_model(self.sounds_model)

    def build_notifications_model_populate_treeview(self):
        # Notification Subscriptions treeview/model
        self.subscriptions_treeview = self.glade.get_widget("subscriptions_treeview")
        subscriptions_selection = self.subscriptions_treeview.get_selection()
        subscriptions_selection.connect(
            "changed", self.on_subscriptions_treeview_selection_changed
        )
        self.subscriptions_treeview.set_tooltip_column(SUB_EVENT_DOC)
        self.subscriptions_model = gtk.ListStore(str, str, bool, bool, bool, bool)

        renderer = gtk.CellRendererText()
        renderer.set_data("event", SUB_EVENT)
        column = gtk.TreeViewColumn("Event", renderer, text=SUB_EVENT)
        column.set_expand(True)
        self.subscriptions_treeview.append_column(column)

        renderer = gtk.CellRendererText()
        renderer.set_data("event_doc", SUB_EVENT)
        column = gtk.TreeViewColumn("Doc", renderer, text=SUB_EVENT_DOC)
        column.set_property('visible', False)
        self.subscriptions_treeview.append_column(column)

        renderer = gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect('toggled', self._on_email_col_toggled)
        column = gtk.TreeViewColumn("Email", renderer, active=SUB_NOT_EMAIL)
        column.set_clickable(True)
        self.subscriptions_treeview.append_column(column)

        renderer = gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect( 'toggled', self._on_popup_col_toggled)
        column = gtk.TreeViewColumn("Popup", renderer, active=SUB_NOT_POPUP)
        column.set_clickable(True)
        self.subscriptions_treeview.append_column(column)

        renderer = gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect( 'toggled', self._on_blink_col_toggled)
        column = gtk.TreeViewColumn("Blink", renderer, active=SUB_NOT_BLINK)
        column.set_clickable(True)
        self.subscriptions_treeview.append_column(column)

        renderer = gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect('toggled', self._on_sound_col_toggled)
        column = gtk.TreeViewColumn("Sound", renderer, active=SUB_NOT_SOUND)
        column.set_clickable(True)
        self.subscriptions_treeview.append_column(column)
        self.subscriptions_treeview.set_model(self.subscriptions_model)

    def popuplate_what_needs_handled_events(self, handled_events,
                                            email_subscriptions=[]):
        self.populate_subscriptions(handled_events, email_subscriptions)
        self.populate_sounds(handled_events)

    def populate_sounds(self, handled_events):
        self.sounds_model.clear()
        for event_name, event_doc in handled_events:
            if event_name in self.config['custom_sounds']:
                snd_path = self.config['custom_sounds'][event_name]
            else:
                snd_path = self.config['sound_path']

            if snd_path:
                self.sounds_model.set(
                    self.sounds_model.append(),
                    SND_EVENT, event_name,
                    SND_EVENT_DOC, event_doc,
                    SND_NAME, basename(snd_path),
                    SND_PATH, snd_path
                )

    def populate_subscriptions(self, handled_events, email_subscriptions=[]):
        subscriptions_dict = self.config['subscriptions']
        self.subscriptions_model.clear()
#        self.handled_events = handled_events
        for event_name, event_doc in handled_events:
            self.subscriptions_model.set(
                self.subscriptions_model.append(),
                SUB_EVENT, event_name,
                SUB_EVENT_DOC, event_doc,
                SUB_NOT_EMAIL, event_name in email_subscriptions,
                SUB_NOT_POPUP, event_name in subscriptions_dict["popup"],
                SUB_NOT_BLINK, event_name in subscriptions_dict['blink'],
                SUB_NOT_SOUND, event_name in subscriptions_dict['sound']
            )


    def on_apply_prefs(self):
        log.debug("applying prefs for Notifications")

        current_popup_subscriptions = []
        current_blink_subscriptions = []
        current_sound_subscriptions = []
        current_email_subscriptions = []
        for event, doc, email, popup, blink, sound in self.subscriptions_model:
            if email:
                current_email_subscriptions.append(event)
            if popup:
                current_popup_subscriptions.append(event)
            if blink:
                current_blink_subscriptions.append(event)
            if sound:
                current_sound_subscriptions.append(event)

        old_sound_file = self.config['sound_path']
        new_sound_file = self.glade.get_widget("sound_path").get_filename()
        log.debug("Old Default sound file: %s New one: %s",
                  old_sound_file, new_sound_file)
        custom_sounds = {}
        for event_name, event_doc, filename, filepath in self.sounds_model:
            log.debug("Custom sound for event \"%s\": %s", event_name, filename)
            if filepath == old_sound_file:
                continue
            custom_sounds[event_name] = filepath

        self.config.config.update({
            "popup_enabled": self.glade.get_widget("popup_enabled").get_active(),
            "blink_enabled": self.glade.get_widget("blink_enabled").get_active(),
            "sound_enabled": self.glade.get_widget("sound_enabled").get_active(),
            "sound_path": new_sound_file,
            "subscriptions": {
                "popup": current_popup_subscriptions,
                "blink": current_blink_subscriptions,
                "sound": current_sound_subscriptions
            },
            "custom_sounds": custom_sounds
        })
        self.config.save()

        core_config = {
            "smtp_enabled": self.glade.get_widget("smtp_enabled").get_active(),
            "smtp_host": self.glade.get_widget("smtp_host").get_text(),
            "smtp_port": self.glade.get_widget("smtp_port").get_value(),
            "smtp_user": self.glade.get_widget("smtp_user").get_text(),
            "smtp_pass": self.glade.get_widget("smtp_pass").get_text(),
            "smtp_from": self.glade.get_widget("smtp_from").get_text(),
            "smtp_tls": self.glade.get_widget("smtp_tls").get_active(),
            "smtp_recipients": [dest[0] for dest in self.recipients_model if
                                dest[0]!='USER@HOST'],
            "subscriptions": {"email": current_email_subscriptions}
        }

        client.notifications.set_config(core_config)
        client.notifications.get_config().addCallback(self.cb_get_config)

    def on_show_prefs(self):
        client.notifications.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, core_config):
        "callback for on show_prefs"
        self.glade.get_widget("smtp_host").set_text(core_config["smtp_host"])
        self.glade.get_widget("smtp_port").set_value(core_config["smtp_port"])
        self.glade.get_widget("smtp_user").set_text(core_config["smtp_user"])
        self.glade.get_widget("smtp_pass").set_text(core_config["smtp_pass"])
        self.glade.get_widget("smtp_from").set_text(core_config["smtp_from"])
        self.glade.get_widget("smtp_tls").set_active(core_config["smtp_tls"])
        self.recipients_model.clear()
        for recipient in core_config['smtp_recipients']:
            self.recipients_model.set(self.recipients_model.append(),
                                      RECIPIENT_FIELD, recipient,
                                      RECIPIENT_EDIT, False)
        self.glade.get_widget("smtp_enabled").set_active(
            core_config['smtp_enabled']
        )
        self.glade.get_widget("sound_enabled").set_active(
            self.config['sound_enabled']
        )
        self.glade.get_widget("popup_enabled").set_active(
            self.config['popup_enabled']
        )
        self.glade.get_widget("blink_enabled").set_active(
            self.config['blink_enabled']
        )
        if self.config['sound_path']:
            sound_path = self.config['sound_path']
        else:
            sound_path = deluge.common.get_default_download_dir()
        self.glade.get_widget("sound_path").set_filename(sound_path)
        # Force toggle
        self.on_enabled_toggled(self.glade.get_widget("smtp_enabled"))
        self.on_sound_enabled_toggled(self.glade.get_widget('sound_enabled'))

        client.notifications.get_handled_events().addCallback(
            self.popuplate_what_needs_handled_events,
            core_config['subscriptions']['email']
        )

    def on_sound_path_update_preview(self, filechooser):
        client.notifications.get_handled_events().addCallback(
            self.populate_sounds
        )

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
        iter = model.get_iter_from_string(path_string)
        path = model.get_path(iter)[0]
        model.set(iter, RECIPIENT_FIELD, new_text)

    def on_recipients_treeview_selection_changed(self, selection):
        model, selected_connection_iter = selection.get_selected()
        if selected_connection_iter:
            self.glade.get_widget("delete_button").set_property('sensitive',
                                                                True)
        else:
            self.glade.get_widget("delete_button").set_property('sensitive',
                                                                False)

    def on_subscriptions_treeview_selection_changed(self, selection):
        model, selected_connection_iter = selection.get_selected()
        if selected_connection_iter:
            self.glade.get_widget("delete_button").set_property('sensitive',
                                                                True)
        else:
            self.glade.get_widget("delete_button").set_property('sensitive',
                                                                False)

    def on_sounds_treeview_selection_changed(self, selection):
        model, iter = selection.get_selected()
        if iter:
            self.glade.get_widget("sounds_edit_button").set_property(
                                                            'sensitive', True)
            path = model.get(iter, SND_PATH)[0]
            log.debug("Sound selection changed: %s", path)
            if path != self.config['sound_path']:
                self.glade.get_widget("sounds_revert_button").set_property(
                                                            'sensitive', True)
            else:
                self.glade.get_widget("sounds_revert_button").set_property(
                                                            'sensitive', False)
        else:
            self.glade.get_widget("sounds_edit_button").set_property(
                                                            'sensitive', False)
            self.glade.get_widget("sounds_revert_button").set_property(
                                                            'sensitive', False)
    def on_sounds_revert_button_clicked(self, widget):
        log.debug("on_sounds_revert_button_clicked")
        selection = self.sounds_treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            log.debug("on_sounds_revert_button_clicked: got iter")
            model.set(iter,
                      SND_PATH, self.config['sound_path'],
                      SND_NAME, basename(self.config['sound_path']))

    def on_sounds_edit_button_clicked(self, widget):
        log.debug("on_sounds_edit_button_clicked")
        selection = self.sounds_treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            path = model.get(iter, SND_PATH)[0]
            dialog = gtk.FileChooserDialog(
                title=_("Choose Sound File"),
                buttons=(gtk.STOCK_CANCEL,
                         gtk.RESPONSE_CANCEL,
                         gtk.STOCK_OPEN,
                         gtk.RESPONSE_OK)
            )
            dialog.set_filename(path)
            def update_model(response):
                if response == gtk.RESPONSE_OK:
                    new_filename = dialog.get_filename()
                    dialog.destroy()
                    print new_filename
                    model.set(iter,
                              SND_PATH, new_filename,
                              SND_NAME, basename(new_filename))
            d = defer.maybeDeferred(dialog.run)
            d.addCallback(update_model)

            log.debug("dialog should have been shown")

    def on_enabled_toggled(self, widget):
        for widget_name in ('smtp_host', 'smtp_port', 'smtp_user', 'smtp_pass',
                            'smtp_pass', 'smtp_tls', 'smtp_from',
                            'smtp_recipients'):
            self.glade.get_widget(widget_name).set_property('sensitive',
                                                            widget.get_active())

    def on_sound_enabled_toggled(self, widget):
        if widget.get_active():
            self.glade.get_widget('sound_path').set_property('sensitive', True)
            self.glade.get_widget('sounds_page').set_property('sensitive',
                                                              True)
            self.glade.get_widget('sounds_page_label').set_property('sensitive',
                                                                    True)
        else:
            self.glade.get_widget('sound_path').set_property('sensitive', False)
            self.glade.get_widget('sounds_page').set_property('sensitive',
                                                              False)
            self.glade.get_widget('sounds_page_label').set_property('sensitive',
                                                                    False)

#        for widget_name in ('sounds_path', 'sounds_page', 'sounds_page_label'):
#            self.glade.get_widget(widget_name).set_property('sensitive',
#                                                            widget.get_active())

    def _on_email_col_toggled(self, cell, path):
        self.subscriptions_model[path][SUB_NOT_EMAIL] = \
            not self.subscriptions_model[path][SUB_NOT_EMAIL]
        return

    def _on_popup_col_toggled(self, cell, path):
        self.subscriptions_model[path][SUB_NOT_POPUP] = \
            not self.subscriptions_model[path][SUB_NOT_POPUP]
        return

    def _on_blink_col_toggled(self, cell, path):
        self.subscriptions_model[path][SUB_NOT_BLINK] = \
            not self.subscriptions_model[path][SUB_NOT_BLINK]
        return

    def _on_sound_col_toggled(self, cell, path):
        self.subscriptions_model[path][SUB_NOT_SOUND] = \
            not self.subscriptions_model[path][SUB_NOT_SOUND]
        return

