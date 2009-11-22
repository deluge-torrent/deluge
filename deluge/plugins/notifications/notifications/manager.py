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


from deluge import component
from deluge.log import LOG as log

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
        log.debug("\n\nNotification success using %s: %s", kind, result)
        return result

    def _on_notify_failure(self, failure, kind):
        log.debug("\n\nNotification failure using %s: %s", kind, failure)
        return failure

    def _on_notify_event_sucess(self, result, kind):
        log.debug("\n\nNotification event success using %s: %s", kind, result)
        return result

    def _on_notify_event_failure(self, failure, kind):
        log.debug("\n\nNotification event failure using %s: %s", kind, failure)
        return failure
