#
# core.py
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
from email.utils import formatdate
from twisted.internet import defer, threads
from deluge import component
from deluge.event import known_events
from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.configmanager
from deluge.core.rpcserver import export

from notifications.common import CustomNotifications

DEFAULT_PREFS = {
    "smtp_enabled": False,
    "smtp_host": "",
    "smtp_port": 25,
    "smtp_user": "",
    "smtp_pass": "",
    "smtp_from": "",
    "smtp_tls": False, # SSL or TLS
    "smtp_recipients": [],
    # Subscriptions
    "subscriptions": {
        "email": []
    }
}

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
        to_addrs = self.config['smtp_recipients']
        to_addrs_str = ', '.join(self.config['smtp_recipients'])
        headers = """\
From: %(smtp_from)s
To: %(smtp_recipients)s
Subject: %(subject)s


""" % {'smtp_from': self.config['smtp_from'],
       'subject': subject,
       'smtp_recipients': to_addrs_str,
       'date': formatdate()
      }

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


class Core(CorePluginBase, CoreNotifications):
    def __init__(self, plugin_name):
        CorePluginBase.__init__(self, plugin_name)
        CoreNotifications.__init__(self)

    def enable(self):
        CoreNotifications.enable(self)
        self.config = deluge.configmanager.ConfigManager(
            "notifications-core.conf", DEFAULT_PREFS)
        log.debug("ENABLING CORE NOTIFICATIONS")

    def disable(self):
        log.debug("DISABLING CORE NOTIFICATIONS")
        CoreNotifications.disable(self)

    @export
    def set_config(self, config):
        "sets the config dictionary"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.config.config

    @export
    def get_handled_events(self):
        return CoreNotifications.get_handled_events(self)
