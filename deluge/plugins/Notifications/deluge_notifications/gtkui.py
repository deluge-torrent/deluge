# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Pedro Algarvio <pedro@algarvio.me>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
from os.path import basename

from gi import require_version
from gi.repository import Gtk
from twisted.internet import defer

import deluge.common
import deluge.component as component
import deluge.configmanager
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client

from .common import CustomNotifications, get_resource

# Relative imports

log = logging.getLogger(__name__)

try:
    import pygame

    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

try:
    require_version('Notify', '0.7')
    from gi.repository import GLib, Notify
except (ValueError, ImportError):
    POPUP_AVAILABLE = False
else:
    POPUP_AVAILABLE = not deluge.common.windows_check()


DEFAULT_PREFS = {
    # BLINK
    'blink_enabled': False,
    # FLASH
    'flash_enabled': False,
    # POPUP
    'popup_enabled': False,
    # SOUND
    'sound_enabled': False,
    'sound_path': '',
    'custom_sounds': {},
    # Subscriptions
    'subscriptions': {'popup': [], 'blink': [], 'sound': []},
}

RECIPIENT_FIELD, RECIPIENT_EDIT = list(range(2))
(
    SUB_EVENT,
    SUB_EVENT_DOC,
    SUB_NOT_EMAIL,
    SUB_NOT_POPUP,
    SUB_NOT_BLINK,
    SUB_NOT_SOUND,
) = list(range(6))
SND_EVENT, SND_EVENT_DOC, SND_NAME, SND_PATH = list(range(4))


class GtkUiNotifications(CustomNotifications):
    def __init__(self, plugin_name=None):
        CustomNotifications.__init__(self, plugin_name)

    def enable(self):
        CustomNotifications.enable(self)
        self.register_custom_blink_notification(
            'TorrentFinishedEvent', self._on_torrent_finished_event_blink
        )
        self.register_custom_sound_notification(
            'TorrentFinishedEvent', self._on_torrent_finished_event_sound
        )
        self.register_custom_popup_notification(
            'TorrentFinishedEvent', self._on_torrent_finished_event_popup
        )

    def disable(self):
        self.deregister_custom_blink_notification('TorrentFinishedEvent')
        self.deregister_custom_sound_notification('TorrentFinishedEvent')
        self.deregister_custom_popup_notification('TorrentFinishedEvent')
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
        return defer.succeed(
            'Will not blink. The returned value from the custom '
            'handler was: %s' % result
        )

    def handle_custom_sound_notification(self, result, eventtype):
        if isinstance(result, ''.__class__):
            if not result and eventtype in self.config['custom_sounds']:
                return defer.maybeDeferred(
                    self.__play_sound, self.config['custom_sounds'][eventtype]
                )
            return defer.maybeDeferred(self.__play_sound, result)
        return defer.succeed(
            'Will not play sound. The returned value from the '
            'custom handler was: %s' % result
        )

    def __blink(self):
        self.systray.blink(True)
        return defer.succeed(_('Notification Blink shown'))

    def __popup(self, title='', message=''):
        if not self.config['popup_enabled']:
            return defer.succeed(_('Popup notification is not enabled.'))
        if not POPUP_AVAILABLE:
            err_msg = _('libnotify is not installed')
            log.warning(err_msg)
            return defer.fail(ImportError(err_msg))

        if Notify.init('Deluge'):
            self.note = Notify.Notification.new(title, message, 'deluge-panel')
            self.note.set_hint('desktop-entry', GLib.Variant.new_string('deluge'))
            if not self.note.show():
                err_msg = _('Failed to popup notification')
                log.warning(err_msg)
                return defer.fail(Exception(err_msg))
        return defer.succeed(_('Notification popup shown'))

    def __play_sound(self, sound_path=''):
        if not self.config['sound_enabled']:
            return defer.succeed(_('Sound notification not enabled'))
        if not SOUND_AVAILABLE:
            err_msg = _('pygame is not installed')
            log.warning(err_msg)
            return defer.fail(ImportError(err_msg))

        pygame.init()
        try:
            if not sound_path:
                sound_path = self.config['sound_path']
            alert_sound = pygame.mixer.music
            alert_sound.load(sound_path)
            alert_sound.play()
        except pygame.error as ex:
            err_msg = _('Sound notification failed %s') % ex
            log.warning(err_msg)
            return defer.fail(ex)
        else:
            msg = _('Sound notification Success')
            log.info(msg)
            return defer.succeed(msg)

    def _on_torrent_finished_event_blink(self, torrent_id):
        return True  # Yes, Blink

    def _on_torrent_finished_event_sound(self, torrent_id):
        # Since there's no custom sound hardcoded, just return ''
        return ''

    def _on_torrent_finished_event_popup(self, torrent_id):
        d = client.core.get_torrent_status(torrent_id, ['name', 'file_progress'])
        d.addCallback(self._on_torrent_finished_event_got_torrent_status)
        d.addErrback(self._on_torrent_finished_event_torrent_status_failure)
        return d

    def _on_torrent_finished_event_torrent_status_failure(self, failure):
        log.debug('Failed to get torrent status to be able to show the popup')

    def _on_torrent_finished_event_got_torrent_status(self, torrent_status):
        log.debug(
            'Handler for TorrentFinishedEvent GTKUI called. ' 'Got Torrent Status'
        )
        title = _('Finished Torrent')
        torrent_status['num_files'] = torrent_status['file_progress'].count(1.0)
        message = (
            _(
                'The torrent "%(name)s" including %(num_files)i file(s) '
                'has finished downloading.'
            )
            % torrent_status
        )
        return title, message


class GtkUI(Gtk3PluginBase, GtkUiNotifications):
    def __init__(self, plugin_name):
        Gtk3PluginBase.__init__(self, plugin_name)
        GtkUiNotifications.__init__(self)

    def enable(self):
        self.config = deluge.configmanager.ConfigManager(
            'notifications-gtk.conf', DEFAULT_PREFS
        )
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('config.ui'))
        self.builder.get_object('smtp_port').set_value(25)
        self.prefs = self.builder.get_object('prefs_box')
        self.prefs.show_all()

        self.build_recipients_model_populate_treeview()
        self.build_sounds_model_populate_treeview()
        self.build_notifications_model_populate_treeview()

        client.notifications.get_handled_events().addCallback(
            self.popuplate_what_needs_handled_events
        )

        self.builder.connect_signals(
            {
                'on_add_button_clicked': (
                    self.on_add_button_clicked,
                    self.recipients_treeview,
                ),
                'on_delete_button_clicked': (
                    self.on_delete_button_clicked,
                    self.recipients_treeview,
                ),
                'on_enabled_toggled': self.on_enabled_toggled,
                'on_sound_enabled_toggled': self.on_sound_enabled_toggled,
                'on_sounds_edit_button_clicked': self.on_sounds_edit_button_clicked,
                'on_sounds_revert_button_clicked': self.on_sounds_revert_button_clicked,
                'on_sound_path_update_preview': self.on_sound_path_update_preview,
            }
        )

        component.get('Preferences').add_page(_('Notifications'), self.prefs)

        component.get('PluginManager').register_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').register_hook(
            'on_show_prefs', self.on_show_prefs
        )

        if not POPUP_AVAILABLE:
            self.builder.get_object('popup_enabled').set_property('sensitive', False)
        if not SOUND_AVAILABLE:
            # for widget_name in ('sound_enabled', 'sound_path', 'sounds_page', 'sounds_page_label'):
            #    self.builder.get_object(widget_name).set_property('sensitive', False)
            self.builder.get_object('sound_enabled').set_property('sensitive', False)
            self.builder.get_object('sound_path').set_property('sensitive', False)
            self.builder.get_object('sounds_page').set_property('sensitive', False)
            self.builder.get_object('sounds_page_label').set_property(
                'sensitive', False
            )

        self.systray = component.get('SystemTray')
        if not hasattr(self.systray, 'tray'):
            # Tray is not beeing used
            self.builder.get_object('blink_enabled').set_property('sensitive', False)

        GtkUiNotifications.enable(self)

    def disable(self):
        GtkUiNotifications.disable(self)
        component.get('Preferences').remove_page(_('Notifications'))
        component.get('PluginManager').deregister_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').deregister_hook(
            'on_show_prefs', self.on_show_prefs
        )

    def build_recipients_model_populate_treeview(self):
        # SMTP Recipients treeview/model
        self.recipients_treeview = self.builder.get_object('smtp_recipients')
        treeview_selection = self.recipients_treeview.get_selection()
        treeview_selection.connect(
            'changed', self.on_recipients_treeview_selection_changed
        )
        self.recipients_model = Gtk.ListStore(str, bool)

        renderer = Gtk.CellRendererText()
        renderer.connect('edited', self.on_cell_edited, self.recipients_model)
        renderer.recipient = RECIPIENT_FIELD
        column = Gtk.TreeViewColumn(
            'Recipients', renderer, text=RECIPIENT_FIELD, editable=RECIPIENT_EDIT
        )
        column.set_expand(True)
        self.recipients_treeview.append_column(column)
        self.recipients_treeview.set_model(self.recipients_model)

    def build_sounds_model_populate_treeview(self):
        # Sound customisation treeview/model
        self.sounds_treeview = self.builder.get_object('sounds_treeview')
        sounds_selection = self.sounds_treeview.get_selection()
        sounds_selection.connect('changed', self.on_sounds_treeview_selection_changed)

        self.sounds_treeview.set_tooltip_column(SND_EVENT_DOC)
        self.sounds_model = Gtk.ListStore(str, str, str, str)

        renderer = Gtk.CellRendererText()
        renderer.event = SND_EVENT
        column = Gtk.TreeViewColumn('Event', renderer, text=SND_EVENT)
        column.set_expand(True)
        self.sounds_treeview.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.event_doc = SND_EVENT_DOC
        column = Gtk.TreeViewColumn('Doc', renderer, text=SND_EVENT_DOC)
        column.set_property('visible', False)
        self.sounds_treeview.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.sound_name = SND_NAME
        column = Gtk.TreeViewColumn('Name', renderer, text=SND_NAME)
        self.sounds_treeview.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.sound_path = SND_PATH
        column = Gtk.TreeViewColumn('Path', renderer, text=SND_PATH)
        column.set_property('visible', False)
        self.sounds_treeview.append_column(column)

        self.sounds_treeview.set_model(self.sounds_model)

    def build_notifications_model_populate_treeview(self):
        # Notification Subscriptions treeview/model
        self.subscriptions_treeview = self.builder.get_object('subscriptions_treeview')
        subscriptions_selection = self.subscriptions_treeview.get_selection()
        subscriptions_selection.connect(
            'changed', self.on_subscriptions_treeview_selection_changed
        )
        self.subscriptions_treeview.set_tooltip_column(SUB_EVENT_DOC)
        self.subscriptions_model = Gtk.ListStore(str, str, bool, bool, bool, bool)

        renderer = Gtk.CellRendererText()
        setattr(renderer, 'event', SUB_EVENT)
        column = Gtk.TreeViewColumn('Event', renderer, text=SUB_EVENT)
        column.set_expand(True)
        self.subscriptions_treeview.append_column(column)

        renderer = Gtk.CellRendererText()
        setattr(renderer, 'event_doc', SUB_EVENT)
        column = Gtk.TreeViewColumn('Doc', renderer, text=SUB_EVENT_DOC)
        column.set_property('visible', False)
        self.subscriptions_treeview.append_column(column)

        renderer = Gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect('toggled', self._on_email_col_toggled)
        column = Gtk.TreeViewColumn('Email', renderer, active=SUB_NOT_EMAIL)
        column.set_clickable(True)
        self.subscriptions_treeview.append_column(column)

        renderer = Gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect('toggled', self._on_popup_col_toggled)
        column = Gtk.TreeViewColumn('Popup', renderer, active=SUB_NOT_POPUP)
        column.set_clickable(True)
        self.subscriptions_treeview.append_column(column)

        renderer = Gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect('toggled', self._on_blink_col_toggled)
        column = Gtk.TreeViewColumn('Blink', renderer, active=SUB_NOT_BLINK)
        column.set_clickable(True)
        self.subscriptions_treeview.append_column(column)

        renderer = Gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect('toggled', self._on_sound_col_toggled)
        column = Gtk.TreeViewColumn('Sound', renderer, active=SUB_NOT_SOUND)
        column.set_clickable(True)
        self.subscriptions_treeview.append_column(column)
        self.subscriptions_treeview.set_model(self.subscriptions_model)

    def popuplate_what_needs_handled_events(
        self, handled_events, email_subscriptions=None
    ):
        if email_subscriptions is None:
            email_subscriptions = []
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
                    SND_EVENT,
                    event_name,
                    SND_EVENT_DOC,
                    event_doc,
                    SND_NAME,
                    basename(snd_path),
                    SND_PATH,
                    snd_path,
                )

    def populate_subscriptions(self, handled_events, email_subscriptions=None):
        if email_subscriptions is None:
            email_subscriptions = []
        subscriptions_dict = self.config['subscriptions']
        self.subscriptions_model.clear()
        #        self.handled_events = handled_events
        for event_name, event_doc in handled_events:
            self.subscriptions_model.set(
                self.subscriptions_model.append(),
                SUB_EVENT,
                event_name,
                SUB_EVENT_DOC,
                event_doc,
                SUB_NOT_EMAIL,
                event_name in email_subscriptions,
                SUB_NOT_POPUP,
                event_name in subscriptions_dict['popup'],
                SUB_NOT_BLINK,
                event_name in subscriptions_dict['blink'],
                SUB_NOT_SOUND,
                event_name in subscriptions_dict['sound'],
            )

    def on_apply_prefs(self):
        log.debug('applying prefs for Notifications')

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
        new_sound_file = self.builder.get_object('sound_path').get_filename()
        log.debug(
            'Old Default sound file: %s New one: %s', old_sound_file, new_sound_file
        )
        custom_sounds = {}
        for event_name, event_doc, filename, filepath in self.sounds_model:
            log.debug('Custom sound for event "%s": %s', event_name, filename)
            if filepath == old_sound_file:
                continue
            custom_sounds[event_name] = filepath

        self.config.config.update(
            {
                'popup_enabled': self.builder.get_object('popup_enabled').get_active(),
                'blink_enabled': self.builder.get_object('blink_enabled').get_active(),
                'sound_enabled': self.builder.get_object('sound_enabled').get_active(),
                'sound_path': new_sound_file,
                'subscriptions': {
                    'popup': current_popup_subscriptions,
                    'blink': current_blink_subscriptions,
                    'sound': current_sound_subscriptions,
                },
                'custom_sounds': custom_sounds,
            }
        )
        self.config.save()

        core_config = {
            'smtp_enabled': self.builder.get_object('smtp_enabled').get_active(),
            'smtp_host': self.builder.get_object('smtp_host').get_text(),
            'smtp_port': self.builder.get_object('smtp_port').get_value(),
            'smtp_user': self.builder.get_object('smtp_user').get_text(),
            'smtp_pass': self.builder.get_object('smtp_pass').get_text(),
            'smtp_from': self.builder.get_object('smtp_from').get_text(),
            'smtp_tls': self.builder.get_object('smtp_tls').get_active(),
            'smtp_recipients': [
                dest[0] for dest in self.recipients_model if dest[0] != 'USER@HOST'
            ],
            'subscriptions': {'email': current_email_subscriptions},
        }

        client.notifications.set_config(core_config)
        client.notifications.get_config().addCallback(self.cb_get_config)

    def on_show_prefs(self):
        client.notifications.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, core_config):
        """Callback for on show_prefs."""
        self.builder.get_object('smtp_host').set_text(core_config['smtp_host'])
        self.builder.get_object('smtp_port').set_value(core_config['smtp_port'])
        self.builder.get_object('smtp_user').set_text(core_config['smtp_user'])
        self.builder.get_object('smtp_pass').set_text(core_config['smtp_pass'])
        self.builder.get_object('smtp_from').set_text(core_config['smtp_from'])
        self.builder.get_object('smtp_tls').set_active(core_config['smtp_tls'])
        self.recipients_model.clear()
        for recipient in core_config['smtp_recipients']:
            self.recipients_model.set(
                self.recipients_model.append(),
                RECIPIENT_FIELD,
                recipient,
                RECIPIENT_EDIT,
                False,
            )
        self.builder.get_object('smtp_enabled').set_active(core_config['smtp_enabled'])
        self.builder.get_object('sound_enabled').set_active(
            self.config['sound_enabled']
        )
        self.builder.get_object('popup_enabled').set_active(
            self.config['popup_enabled']
        )
        self.builder.get_object('blink_enabled').set_active(
            self.config['blink_enabled']
        )
        if self.config['sound_path']:
            sound_path = self.config['sound_path']
        else:
            sound_path = deluge.common.get_default_download_dir()
        self.builder.get_object('sound_path').set_filename(sound_path)
        # Force toggle
        self.on_enabled_toggled(self.builder.get_object('smtp_enabled'))
        self.on_sound_enabled_toggled(self.builder.get_object('sound_enabled'))

        client.notifications.get_handled_events().addCallback(
            self.popuplate_what_needs_handled_events,
            core_config['subscriptions']['email'],
        )

    def on_sound_path_update_preview(self, filechooser):
        client.notifications.get_handled_events().addCallback(self.populate_sounds)

    def on_add_button_clicked(self, widget, treeview):
        model = treeview.get_model()
        model.set(model.append(), RECIPIENT_FIELD, 'USER@HOST', RECIPIENT_EDIT, True)

    def on_delete_button_clicked(self, widget, treeview):
        selection = treeview.get_selection()
        model, selected_iter = selection.get_selected()
        if selected_iter:
            model.remove(selected_iter)

    def on_cell_edited(self, cell, path_string, new_text, model):
        str_iter = model.get_iter_from_string(path_string)
        model.set(str_iter, RECIPIENT_FIELD, new_text)

    def on_recipients_treeview_selection_changed(self, selection):
        model, selected_connection_iter = selection.get_selected()
        if selected_connection_iter:
            self.builder.get_object('delete_button').set_property('sensitive', True)
        else:
            self.builder.get_object('delete_button').set_property('sensitive', False)

    def on_subscriptions_treeview_selection_changed(self, selection):
        model, selected_connection_iter = selection.get_selected()
        if selected_connection_iter:
            self.builder.get_object('delete_button').set_property('sensitive', True)
        else:
            self.builder.get_object('delete_button').set_property('sensitive', False)

    def on_sounds_treeview_selection_changed(self, selection):
        model, selected_iter = selection.get_selected()
        if selected_iter:
            self.builder.get_object('sounds_edit_button').set_property(
                'sensitive', True
            )
            path = model.get(selected_iter, SND_PATH)[0]
            log.debug('Sound selection changed: %s', path)
            if path != self.config['sound_path']:
                self.builder.get_object('sounds_revert_button').set_property(
                    'sensitive', True
                )
            else:
                self.builder.get_object('sounds_revert_button').set_property(
                    'sensitive', False
                )
        else:
            self.builder.get_object('sounds_edit_button').set_property(
                'sensitive', False
            )
            self.builder.get_object('sounds_revert_button').set_property(
                'sensitive', False
            )

    def on_sounds_revert_button_clicked(self, widget):
        log.debug('on_sounds_revert_button_clicked')
        selection = self.sounds_treeview.get_selection()
        model, selected_iter = selection.get_selected()
        if selected_iter:
            log.debug('on_sounds_revert_button_clicked: got iter')
            model.set(
                selected_iter,
                SND_PATH,
                self.config['sound_path'],
                SND_NAME,
                basename(self.config['sound_path']),
            )

    def on_sounds_edit_button_clicked(self, widget):
        log.debug('on_sounds_edit_button_clicked')
        selection = self.sounds_treeview.get_selection()
        model, selected_iter = selection.get_selected()
        if selected_iter:
            path = model.get(selected_iter, SND_PATH)[0]
            dialog = Gtk.FileChooserDialog(
                title=_('Choose Sound File'),
                buttons=(
                    Gtk.STOCK_CANCEL,
                    Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_OPEN,
                    Gtk.ResponseType.OK,
                ),
            )
            dialog.set_filename(path)

            def update_model(response):
                if response == Gtk.ResponseType.OK:
                    new_filename = dialog.get_filename()
                    dialog.destroy()
                    log.debug(new_filename)
                    model.set(
                        selected_iter,
                        SND_PATH,
                        new_filename,
                        SND_NAME,
                        basename(new_filename),
                    )

            d = defer.maybeDeferred(dialog.run)
            d.addCallback(update_model)

            log.debug('dialog should have been shown')

    def on_enabled_toggled(self, widget):
        for widget_name in (
            'smtp_host',
            'smtp_port',
            'smtp_user',
            'smtp_pass',
            'smtp_pass',
            'smtp_tls',
            'smtp_from',
            'smtp_recipients',
        ):
            self.builder.get_object(widget_name).set_property(
                'sensitive', widget.get_active()
            )

    def on_sound_enabled_toggled(self, widget):
        if widget.get_active():
            self.builder.get_object('sound_path').set_property('sensitive', True)
            self.builder.get_object('sounds_page').set_property('sensitive', True)
            self.builder.get_object('sounds_page_label').set_property('sensitive', True)
        else:
            self.builder.get_object('sound_path').set_property('sensitive', False)
            self.builder.get_object('sounds_page').set_property('sensitive', False)
            self.builder.get_object('sounds_page_label').set_property(
                'sensitive', False
            )

    #        for widget_name in ('sounds_path', 'sounds_page', 'sounds_page_label'):
    #            self.builder.get_object(widget_name).set_property('sensitive',
    #                                                            widget.get_active())

    def _on_email_col_toggled(self, cell, path):
        self.subscriptions_model[path][SUB_NOT_EMAIL] = not self.subscriptions_model[
            path
        ][SUB_NOT_EMAIL]
        return

    def _on_popup_col_toggled(self, cell, path):
        self.subscriptions_model[path][SUB_NOT_POPUP] = not self.subscriptions_model[
            path
        ][SUB_NOT_POPUP]
        return

    def _on_blink_col_toggled(self, cell, path):
        self.subscriptions_model[path][SUB_NOT_BLINK] = not self.subscriptions_model[
            path
        ][SUB_NOT_BLINK]
        return

    def _on_sound_col_toggled(self, cell, path):
        self.subscriptions_model[path][SUB_NOT_SOUND] = not self.subscriptions_model[
            path
        ][SUB_NOT_SOUND]
        return
