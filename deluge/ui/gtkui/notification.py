# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Marcos Pinto ('markybob') <markybob@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.ui.gtkui.common import get_logo

log = logging.getLogger(__name__)


class Notification:
    def __init__(self):
        self.config = ConfigManager("gtkui.conf")
        self.tray = component.get("SystemTray")

    def notify(self, torrent_id):
        if self.config["ntf_tray_blink"]:
            self.tray.blink(True)
        if self.config["ntf_popup"] or self.config["ntf_email"]:
            self.get_torrent_status(torrent_id)

    def get_torrent_status(self, torrent_id):
        component.get("SessionProxy").get_torrent_status(torrent_id, [
            "name", "num_files", "total_payload_download"
        ]).addCallback(self._on_get_torrent_status)

    def _on_get_torrent_status(self, status):
        if status is None:
            return
        if status["total_payload_download"]:
            if self.config["ntf_popup"]:
                self.popup(status)
            if self.config["ntf_email"]:
                self.email(status)
            if self.config["ntf_sound"]:
                self.sound()

    def popup(self, status):
        """popups up notification of finished torrent"""
        if not deluge.common.windows_check():
            try:
                from gi.repository import Notify
            except:
                log.warning("pynotify is not installed")
            else:
                if not Notify.init("Deluge"):
                    return
                title = deluge.common.xml_encode(_("Torrent complete"))
                message = deluge.common.xml_encode("%s\n%s %i %s" % (status["name"],
                                                   _("Including"), status["num_files"], _("files")))
                self.note = Notify.Notification(title, message)
                self.note.set_icon_from_pixbuf(get_logo(48))
                if not self.note.show():
                    log.warning("pynotify failed to show notification")

    def sound(self):
        """plays a sound when a torrent finishes"""
        try:
            import pygame
        except:
            log.warning("pygame is not installed")
        else:
            pygame.init()
            try:
                alert_sound = pygame.mixer.music
                alert_sound.load(self.config["ntf_sound_path"])
                alert_sound.play()
            except pygame.error as ex:
                log.warning("pygame failed to play because %s", ex)
            else:
                log.info("sound notification played successfully")

    def email(self, status):
        """sends email notification of finished torrent"""
        import smtplib
        headers = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (
            self.config["ntf_email_add"], self.config["ntf_email_add"],
            "Finished torrent %s" % (status["name"]))
        text = _("This email is to inform you that Deluge has finished "
                 "downloading %(name)s , which includes %(num_files)i files.\n"
                 "To stop receiving these alerts, simply turn off email "
                 "notification in Deluge's preferences.\n\n"
                 "Thank you,\nDeluge") % {"name": status["name"],
                                          "num_files": status["num_files"]}
        message = headers + text
        if self.config["ntf_security"] == 'SSL':
            port = 465
        elif self.config["ntf_security"] == 'TLS':
            port = 587
        elif self.config["ntf_security"] is None:
            port = 25
        try:
            mail_server = smtplib.SMTP(self.config["ntf_server"], port)
        except Exception as ex:
            log.error("There was an error sending the notification email: %s", ex)
            return

        if self.config["ntf_username"] and self.config["ntf_pass"]:
            if self.config["ntf_security"] == 'SSL' or 'TLS':
                mail_server.ehlo('x')
                mail_server.starttls()
                mail_server.ehlo('x')
            try:
                mail_server.login(self.config["ntf_username"], self.config["ntf_pass"])
            except smtplib.SMTPHeloError:
                log.warning("The server didn't reply properly to the helo greeting")
            except smtplib.SMTPAuthenticationError:
                log.warning("The server didn't accept the username/password combination")
        try:
            mail_server.sendmail(self.config["ntf_email_add"], self.config["ntf_email_add"], message)
            mail_server.quit()
        except:
            log.warning("sending email notification of finished torrent failed")
        else:
            log.info("sending email notification of finished torrent was successful")
