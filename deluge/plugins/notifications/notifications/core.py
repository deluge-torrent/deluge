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
from twisted.internet import defer, threads
from deluge.event import known_events, DelugeEvent
from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

from test import TestEmailNotifications

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

class Core(CorePluginBase, component.Component):
    def __init__(self, plugin_name):
        CorePluginBase.__init__(self, plugin_name)
        component.Component.__init__(self, "Notifications")
        self.email_message_providers = {}
        self.tn = TestEmailNotifications()

    def enable(self):
        self.config = deluge.configmanager.ConfigManager(
            "notifications-core.conf", DEFAULT_PREFS)
        component.get("EventManager").register_event_handler(
            "TorrentFinishedEvent", self._on_torrent_finished_event
        )
        log.debug("\n\nENABLING CORE NOTIFICATIONS\n\n")
        self.tn.enable()
#        import sys
#        print '\n\n', [(n, k.__module__) for n, k in known_events.items()]
#        print [f for f in sys.modules.keys() if f.startswith("deluge.event")]

    def disable(self):
        self.tn.disable()
        log.debug("\n\nDISABLING CORE NOTIFICATIONS\n\n")
        for eventtype in self.email_message_providers.keys():
            self.deregister_email_message_provider(eventtype)

    def update(self):
        pass

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
        handled_events = []
        for evt in sorted(known_events.keys()):
            if known_events[evt].__module__.startswith('deluge.event'):
                if evt not in ('TorrentFinishedEvent',):
                    # Skip the base class for all events
                    continue
            classdoc = known_events[evt].__doc__.strip()
            handled_events.append((evt, classdoc))
        log.debug("Handled Notification Events: %s", handled_events)
        return handled_events

    def register_email_message_provider(self, eventtype, handler):
        """This is used to register email formatters for custom event types.

        :param event: str, the event name
        :param handler: function, to be called when `:param:event` is emitted

        You're handler should return a tuple of (subject, email_contents).
        """
        if eventtype not in known_events:
            raise Exception("The event \"%s\" is not known" % eventtype)
        if known_events[eventtype].__module__.startswith('deluge.event'):
            raise Exception("You cannot register email message providers for "
                            "built-in event types.")
        if eventtype not in self.email_message_providers:
            def wrapper(*args, **kwargs):
                return self._handle_custom_email_message_providers(eventtype,
                                                                   *args,
                                                                   **kwargs)
            self.email_message_providers[eventtype] = (wrapper, handler)
        else:
            wrapper, handler = self.email_message_providers[eventtype]
        component.get("EventManager").register_event_handler(
            eventtype, wrapper
        )

    def deregister_email_message_provider(self, eventtype):
        wrapper, handler = self.email_message_providers[eventtype]
        component.get("EventManager").deregister_event_handler(
            eventtype, wrapper
        )
        self.email_message_providers.pop(eventtype)

    def _handle_custom_email_message_providers(self, event, *args, **kwargs):
        if not self.config['smtp_enabled']:
            return defer.succeed("SMTP notification not enabled.")

        log.debug("\n\nCalling CORE's custom email providers for %s: %s %s",
                  event, args, kwargs)
        if event in self.config["subscriptions"]["email"]:
            wrapper, handler = self.email_message_providers[event]
            log.debug("Found handler: %s", handler)
            d = defer.maybeDeferred(handler, *args, **kwargs)
            d.addCallback(self._prepare_email)
            d.addCallback(self._on_notify_sucess)
            d.addErrback(self._on_notify_failure)
            return d


    def _prepare_email(self, result):
        if not self.config['smtp_enabled']:
            return defer.succeed("SMTP notification not enabled.")
        subject, message = result
        log.debug("\n\nSending email with subject: %s: %s", subject, message)
        return threads.deferToThread(self._notify_email, subject, message)


    def _notify_email(self, subject='', message=''):
        log.debug("Email prepared")
        config = self.config
        to_addrs = '; '.join(config['smtp_recipients'])
        headers = """\
From: %(smtp_from)s
To: %(smtp_recipients)s
Subject: %(subject)s


""" % {'smtp_from': config['smtp_from'],
       'subject': subject,
       'smtp_recipients': to_addrs}

        message = '\r\n'.join((headers + message).splitlines())

        try:
            server = smtplib.SMTP(config["smtp_host"], config["smtp_port"])
        except Exception, err:
            err_msg = _("There was an error sending the notification email:"
                        " %s") % err
            log.error(err_msg)
            return err

        security_enabled = config['smtp_tls']

        if security_enabled:
            server.ehlo()
            if not server.esmtp_features.has_key('starttls'):
                log.warning("TLS/SSL enabled but server does not support it")
            else:
                server.starttls()
                server.ehlo()

        if config['smtp_user'] and config['smtp_pass']:
            try:
                server.login(config['smtp_user'], config['smtp_pass'])
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
                server.sendmail(config['smtp_from'], to_addrs, message)
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
        log.debug("\n\nHandler for TorrentFinishedEvent called for CORE")
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

        d = defer.maybeDeferred(self._prepare_email, [subject, message])
        d.addCallback(self._on_notify_sucess)
        d.addErrback(self._on_notify_failure)
        return d


    def _on_notify_sucess(self, result):
        log.debug("\n\nEMAIL Notification success: %s", result)
        return result


    def _on_notify_failure(self, failure):
        log.debug("\n\nEMAIL Notification failure: %s", failure)
        return failure
