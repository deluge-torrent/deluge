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
from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

# Relative imports
from manager import Notifications
import events

DEFAULT_PREFS = {
    # BLINK
    "blink_enabled": False,
    # EMAIL
    "smtp_enabled": False,
    "smtp_host": "",
    "smtp_port": 25,
    "smtp_user": "",
    "smtp_pass": "",
    "smtp_from": "",
    "smtp_tls": False, # SSL or TLS
    "smtp_recipients": [],
    # FLASH
    "flash_enabled": False,
    # POPUP
    "popup_enabled": False,
    # SOUND
    "sound_enabled": False,
    "sound_path": ""
}


class Core(CorePluginBase, Notifications):
    def enable(self):
        Notifications.enable(self)
        self.config = deluge.configmanager.ConfigManager("notifications.conf",
                                                         DEFAULT_PREFS)
        component.get("EventManager").register_event_handler(
            "TorrentFinishedEvent", self._on_torrent_finished_event
        )
        log.debug("\n\nENABLING CORE NOTIFICATIONS\n\n")

    def disable(self):
        Notifications.disable(self)
        log.debug("\n\nDISABLING CORE NOTIFICATIONS\n\n")

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

    # Notification methods
    @export
    def notify_blink(self):
        if not self.config["blink_enabled"]:
            return defer.succeed("Blink notification not enabled")
        return defer.maybeDeferred(
            component.get("EventManager").emit, events.NotificationBlinkEvent())

    @export
    def notify_email(self, title='', message='', smtp_from='', recipients=[]):
        if not self.config['smtp_enabled']:
            return defer.succeed("SMTP notification not enabled")
        d = threads.deferToThread(self._notify_email, title, message, smtp_from,
                                  recipients)
        d.addCallback(self._on_notify_sucess, 'email')
        d.addErrback(self._on_notify_failure, 'email')
        return d

    @export
    def notify_flash(self, title='', message=''):
        if not self.config["flash_enabled"]:
            return defer.succeed("Flash notification not enabled")
        return defer.maybeDeferred(
            component.get("EventManager").emit,
            events.NotificationFlashEvent(title, message)
        )

    @export
    def notify_popup(self, title='', message=''):
        if not self.config["popup_enabled"]:
            return defer.succeed("Popup notification not enabled")
        return defer.maybeDeferred(
            component.get("EventManager").emit,
            events.NotificationPopupEvent(title, message)
        )

    @export
    def notify_sound(self, sound_path=''):
        if not self.config["sound_enabled"]:
            return defer.succeed("Sound notification not enabled")
        return defer.maybeDeferred(
            component.get("EventManager").emit,
            events.NotificationSoundEvent(sound_path))

    def _notify_email(self, title='', message='', smtp_from='', recipients=[]):
        config = self.config
        to_addrs = '; '.join(config['smtp_recipients']+recipients)
        headers = """\
From: %(smtp_from)s
To: %(smtp_recipients)s
Subject: %(title)s


""" % {'smtp_from': smtp_from and smtp_from or config['smtp_from'],
       'title': title,
       'smtp_recipients': to_addrs}

        message = '\r\n'.join((headers + message).splitlines())

        try:
            server = smtplib.SMTP(config["smtp_host"], config["smtp_port"])
        except Exception, err:
            log.error("There was an error sending the notification email: %s",
                      err)

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
            except smtplib.SMTPHeloError:
                log.warning("The server didn't reply properly to the helo "
                            "greeting")
            except smtplib.SMTPAuthenticationError:
                log.warning("The server didn't accept the username/password "
                            "combination")

        try:
            try:
                server.sendmail(config['smtp_from'], to_addrs, message)
            except smtplib.SMTPException, err:
                log.error("There was an error sending the notification email: "
                          "%s", err)
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
        return "Notification email sent."
