#
# common.py
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

import smtplib
from twisted.internet import defer, threads
from deluge import component
from deluge.event import known_events
from deluge.log import LOG as log
from deluge.ui.client import client
import deluge.common

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


def get_resource(filename):
    import pkg_resources, os
    return pkg_resources.resource_filename("notifications",
                                           os.path.join("data", filename))


class CustomNotifications(object):
    config = None   # shut-up pylint

    def __init__(self, plugin_name=None):
        self.custom_notifications = {
            "email": {},
            "popup": {},
            "blink": {},
            "sound": {}
        }

    def enable(self):
        pass

    def disable(self):
        for kind in self.custom_notifications.iterkeys():
            for eventtype in self.custom_notifications[kind].copy().iterkeys():
                wrapper, handler = self.custom_notifications[kind][eventtype]
                self._deregister_custom_provider(kind, eventtype)

    def _handle_custom_providers(self, kind, eventtype, *args, **kwargs):
        log.debug("Calling CORE's custom %s providers for %s: %s %s",
                  kind, eventtype, args, kwargs)
        if eventtype in self.config["subscriptions"][kind]:
            wrapper, handler = self.custom_notifications[kind][eventtype]
            log.debug("Found handler for kind %s: %s", kind, handler)
            custom_notif_func = getattr(self,
                                        'handle_custom_%s_notification' % kind)
            d = defer.maybeDeferred(handler, *args, **kwargs)
            d.addCallback(custom_notif_func, eventtype)
            d.addCallback(self._on_notify_sucess, kind)
            d.addErrback(self._on_notify_failure, kind)
            return d

    def _register_custom_provider(self, kind, eventtype, handler):
        if not self._handled_eventtype(eventtype, handler):
            return defer.succeed("Event not handled")
        if eventtype not in self.custom_notifications:
            def wrapper(*args, **kwargs):
                return self._handle_custom_providers(kind, eventtype,
                                                      *args, **kwargs)
            self.custom_notifications[kind][eventtype] = (wrapper, handler)
        else:
            wrapper, handler = self.custom_notifications[kind][eventtype]
        try:
            component.get("EventManager").register_event_handler(
                eventtype, wrapper
            )
        except KeyError:
            from deluge.ui.client import client
            client.register_event_handler(eventtype, wrapper)

    def _deregister_custom_provider(self, kind, eventtype):
        wrapper, handler = self.custom_notifications[kind][eventtype]
        try:
            component.get("EventManager").deregister_event_handler(
                eventtype, wrapper
            )
        except KeyError:
            from deluge.ui.client import client
            client.deregister_event_handler(eventtype, wrapper)
        self.custom_notifications[kind].pop(eventtype)

    def _handled_eventtype(self, eventtype, handler):
        if eventtype not in known_events:
            log.error("The event \"%s\" is not known" % eventtype)
            return False
        if known_events[eventtype].__module__.startswith('deluge.event'):
            if handler.im_self is self:
                return True
            log.error("You cannot register custom notification providers "
                      "for built-in event types.")
            return False
        return True

    def _on_notify_sucess(self, result, kind):
        log.debug("Notification success using %s: %s", kind, result)
        return result

    def _on_notify_failure(self, failure, kind):
        log.debug("Notification failure using %s: %s", kind, failure)
        return failure


class CoreNotifications(CustomNotifications):

    def enable(self):
        CustomNotifications.enable(self)
        self.register_custom_email_notification('TorrentFinishedEvent',
                                                self._on_torrent_finished_event)

    def disable(self):
        self.deregister_custom_email_notification('TorrentFinishedEvent')
        CustomNotifications.disable(self)

    def register_custom_email_notification(self, eventtype, handler):
        """This is used to register email notifications for custom event types.

        :param event: str, the event name
        :param handler: function, to be called when `:param:event` is emitted

        Your handler should return a tuple of (email_subject, email_contents).
        """
        self._register_custom_provider('email', eventtype, handler)

    def deregister_custom_email_notification(self, eventtype):
        self._deregister_custom_provider('email', eventtype)

    def handle_custom_email_notification(self, result, eventtype):
        if not self.config['smtp_enabled']:
            return defer.succeed("SMTP notification not enabled.")
        subject, message = result
        log.debug("Spawning new thread to send email with subject: %s: %s",
                  subject, message)
        # Spawn thread because we don't want Deluge to lock up while we send the
        # email.
        return threads.deferToThread(self._notify_email, subject, message)

    def get_handled_events(self):
        handled_events = []
        for evt in sorted(known_events.keys()):
            if known_events[evt].__module__.startswith('deluge.event'):
                if evt not in ('TorrentFinishedEvent',):
                    # Skip all un-handled built-in events
                    continue
            classdoc = known_events[evt].__doc__.strip()
            handled_events.append((evt, classdoc))
        log.debug("Handled Notification Events: %s", handled_events)
        return handled_events

    def _notify_email(self, subject='', message=''):
        log.debug("Email prepared")
        to_addrs = '; '.join(self.config['smtp_recipients'])
        headers = """\
From: %(smtp_from)s
To: %(smtp_recipients)s
Subject: %(subject)s


""" % {'smtp_from': self.config['smtp_from'],
       'subject': subject,
       'smtp_recipients': to_addrs}

        message = '\r\n'.join((headers + message).splitlines())

        try:
            try:
                # Python 2.6
                server = smtplib.SMTP(self.config["smtp_host"],
                                      self.config["smtp_port"],
                                      timeout=60)
            except:
                # Python 2.5
                server = smtplib.SMTP(self.config["smtp_host"],
                                      self.config["smtp_port"])
        except Exception, err:
            err_msg = _("There was an error sending the notification email:"
                        " %s") % err
            log.error(err_msg)
            return err

        security_enabled = self.config['smtp_tls']

        if security_enabled:
            server.ehlo()
            if not server.esmtp_features.has_key('starttls'):
                log.warning("TLS/SSL enabled but server does not support it")
            else:
                server.starttls()
                server.ehlo()

        if self.config['smtp_user'] and self.config['smtp_pass']:
            try:
                server.login(self.config['smtp_user'], self.config['smtp_pass'])
            except smtplib.SMTPHeloError, err:
                err_msg = _("The server didn't reply properly to the helo "
                            "greeting: %s") % err
                log.error(err_msg)
                return err
            except smtplib.SMTPAuthenticationError, err:
                err_msg = _("The server didn't accept the username/password "
                            "combination: %s") % err
                log.error(err_msg)
                return err

        try:
            try:
                server.sendmail(self.config['smtp_from'], to_addrs, message)
            except smtplib.SMTPException, err:
                err_msg = _("There was an error sending the notification email:"
                            " %s") % err
                log.error(err_msg)
                return err
        finally:
            if security_enabled:
                # avoid false failure detection when the server closes
                # the SMTP connection with TLS enabled
                import socket
                try:
                    server.quit()
                except socket.sslerror:
                    pass
            else:
                server.quit()
        return _("Notification email sent.")


    def _on_torrent_finished_event(self, torrent_id):
        log.debug("Handler for TorrentFinishedEvent called for CORE")
        torrent = component.get("TorrentManager")[torrent_id]
        torrent_status = torrent.get_status({})
        # Email
        subject = _("Finished Torrent \"%(name)s\"") % torrent_status
        message = _(
            "This email is to inform you that Deluge has finished "
            "downloading \"%(name)s\", which includes %(num_files)i files."
            "\nTo stop receiving these alerts, simply turn off email "
            "notification in Deluge's preferences.\n\n"
            "Thank you,\nDeluge."
        ) % torrent_status
        return subject, message

        d = defer.maybeDeferred(self.handle_custom_email_notification,
                                [subject, message],
                                "TorrentFinishedEvent")
        d.addCallback(self._on_notify_sucess, 'email')
        d.addErrback(self._on_notify_failure, 'email')
        return d


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
        d = client.core.get_torrent_status(torrent_id, ["name", "num_files"])
        d.addCallback(self._on_torrent_finished_event_got_torrent_status)
        d.addErrback(self._on_torrent_finished_event_torrent_status_failure)
        return d

    def _on_torrent_finished_event_torrent_status_failure(self, failure):
        log.debug("Failed to get torrent status to be able to show the popup")

    def _on_torrent_finished_event_got_torrent_status(self, torrent_status):
        log.debug("Handler for TorrentFinishedEvent GTKUI called. "
                  "Got Torrent Status")
        title = _("Finished Torrent")
        message = _("The torrent \"%(name)s\" including %(num_files)i "
                    "has finished downloading.") % torrent_status
        return title, message


