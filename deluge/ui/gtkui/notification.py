#
# notification.py
#
# Copyright (C) 2008 Marcos Mobley ('markybob') <markybob@gmail.com>
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
#


import deluge.component as component
import deluge.common
import common
from deluge.log import LOG as log
from deluge.configmanager import ConfigManager
from deluge.ui.client import client

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
        component.get("SessionProxy").get_torrent_status(torrent_id, ["name", "num_files", "total_payload_download"]).addCallback(self._on_get_torrent_status)

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
                import pynotify
            except:
                log.warning("pynotify is not installed")
            else:
                if not pynotify.init("Deluge"):
                    return
                title = deluge.common.xml_encode(_("Torrent complete"))
                message = deluge.common.xml_encode("%s\n%s %i %s"  % (status["name"], _("Including"), status["num_files"], _("files")))
                self.note = pynotify.Notification(title, message)
                self.note.set_icon_from_pixbuf(common.get_logo(48))
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
            except pygame.error, message:
                log.warning("pygame failed to play because %s" % (message))
            else:
                log.info("sound notification played successfully")

    def email(self, status):
        """sends email notification of finished torrent"""
        import smtplib
        headers = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (
            self.config["ntf_email_add"], self.config["ntf_email_add"],
                "Finished torrent %s" % (status["name"]))
        text = _("This email is to inform you that Deluge has finished downloading %(name)s , \
            which includes %(num_files)i files.\nTo stop receiving these alerts, simply turn off \
            email notification in Deluge's preferences.\n\nThank you,\nDeluge") % {"name": status["name"], "num_files": status["num_files"]}
        message = headers + text
        if self.config["ntf_security"] == 'SSL':
            port = 465
        elif self.config["ntf_security"] == 'TLS':
            port = 587
        elif self.config["ntf_security"] == None:
            port = 25
        try:
            mailServer = smtplib.SMTP(self.config["ntf_server"], port)
        except Exception, e:
            log.error("There was an error sending the notification email: %s", e)
            return

        if self.config["ntf_username"] and self.config["ntf_pass"]:
            if self.config["ntf_security"] == 'SSL' or 'TLS':
                mailServer.ehlo('x')
                mailServer.starttls()
                mailServer.ehlo('x')
            try:
                mailServer.login(self.config["ntf_username"], self.config["ntf_pass"])
            except smtplib.SMTPHeloError:
                log.warning("The server didn't reply properly to the helo greeting")
            except smtplib.SMTPAuthenticationError:
                log.warning("The server didn't accept the username/password combination")
        try:
            mailServer.sendmail(self.config["ntf_email_add"], self.config["ntf_email_add"], message)
            mailServer.quit()
        except:
            log.warning("sending email notification of finished torrent failed")
        else:
            log.info("sending email notification of finished torrent was successful")
