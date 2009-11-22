#
# notifications.py
#
# Copyright (C) 2009 Pedro Algarvio <ufs@ufsoft.org>
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
#


from twisted.internet import defer, threads
from deluge import component
from deluge.core.rpcserver import export
from deluge.log import LOG as log
from deluge.ui.client import client


class Notifications(component.Component):
    def __init__(self, name):
        component.Component.__init__(self, "Notifications")
        log.debug("\n\nSTARTING NOTIFICATIONS\n\n")

    def enable(self):
        log.debug("\n\nENABLING NOTIFICATIONS\n\n")

    def disable(self):
        log.debug("\n\nDISABLING NOTIFICATIONS\n\n")


    def notify_blink(self):
        raise NotImplementedError("%s has not implemented this method" %
                                  self.__class__.__name__)

    def notify_email(self, title='', message='', smtp_from='', recipients=[]):
        raise NotImplementedError("%s has not implemented this method" %
                                  self.__class__.__name__)

    def notify_flash(self, title='', message=''):
        raise NotImplementedError("%s has not implemented this method" %
                                  self.__class__.__name__)

    def notify_popup(self, title='', message=''):
        raise NotImplementedError("%s has not implemented this method" %
                                  self.__class__.__name__)

    def notify_sound(self, sound_path=''):
        raise NotImplementedError("%s has not implemented this method" %
                                  self.__class__.__name__)

    def notify(self,
               # COMMON
               title = '', message='',
               # EMAIL
               smtp_from='', recipients=[],
               # SOUND
               sound_path=''):
        self.notify_blink()
        self.notify_email(title, message, smtp_from, recipients)
        self.notify_flash(title, message)
        self.notify_popup(title, message)
        self.notify_sound(sound_path)

    def _on_notify_sucess(self, result, kind):
        log.debug("Notification success using %s: %s", kind, result)

    def _on_notify_failure(self, failure, kind):
        log.debug("Notification failure using %s: %s", kind, failure)

#    def _on_torrent_finished_event(self, torrent_id):
#        log.debug("\n\nhandler for TorrentFinishedEvent called")
#        torrent = component.get("TorrentManager")[torrent_id]
#        torrent_status = torrent.get_status({})
#        # Email
#        title = _("Finished Torrent %(name)s") % torrent_status
#        message = _(
#            "This email is to inform you that Deluge has finished "
#            "downloading \"%(name)s\", which includes %(num_files)i files."
#            "\nTo stop receiving these alerts, simply turn off email "
#            "notification in Deluge's preferences.\n\n"
#            "Thank you,\nDeluge."
#        ) % torrent_status
#
#        d0 = defer.maybeDeferred(self.notify_blink)
#        d0.addCallback(self._on_notify_sucess, 'blink')
#        d0.addErrback(self._on_notify_failure, 'blink')
#        log.debug("Blink notification callback yielded")
#
##        self.notify_email(title, message)
#        d1 = defer.maybeDeferred(self.notify_email, title, message)
#        d1.addCallback(self._on_notify_sucess, 'email')
#        d1.addErrback(self._on_notify_failure, 'email')
##        d.
##        yield d
#        log.debug("Email notification callback yielded")
#
#        d2 = defer.maybeDeferred(self.notify_flash, title, message)
#        d2.addCallback(self._on_notify_sucess, 'flash')
#        d2.addErrback(self._on_notify_failure, 'flash')
##        d.
##        yield d
#        log.debug("Flash notification callback yielded")
#        # Sound
##        self.notify_sound()
#        d3 = defer.maybeDeferred(self.notify_sound)
#        d3.addCallback(self._on_notify_sucess, 'sound')
#        d3.addErrback(self._on_notify_failure, 'sound')
##        yield d
#        log.debug("Sound notification callback yielded")
#
#        # Popup
#        title = _("Finished Torrent")
#        message = _("The torrent \"%(name)s\" including %(num_files)i "
#                    "has finished downloading.") % torrent_status
##        self.notify_popup(title, message)
#        d4 = defer.maybeDeferred(self.notify_popup, title, message)
#        d4.addCallback(self._on_notify_sucess, 'popup')
#        d4.addErrback(self._on_notify_failure, 'popup')
##        yield d
#        log.debug("Popup notification callback yielded")
#
#        d5 = defer.maybeDeferred(self.notify_sound)
#        d5.addCallback(self._on_notify_sucess, 'sound')
#        d5.addErrback(self._on_notify_failure, 'sound')
