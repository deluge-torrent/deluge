#
# events.py
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

from deluge.event import DelugeEvent

class NotificationEvent(DelugeEvent):
    """Emitted when a notification is suposed to happen."""
    def __init__(self, title=None, message=None):
        """
        :param title: the notification title
        :type title: string
        :param message: the notification message
        :type message: string
        """
        self._args = [title, message]

class NotificationBlinkEvent(DelugeEvent):
    """Emitted when a tray icon blink should occur."""

class NotificationPopupEvent(DelugeEvent):
    """Emitted when a popup notification is required"""
    def __init__(self, title="", message=""):
        """
        :param title: the notification title
        :type title: string
        :param message: the notification message
        :type message: string
        """
        self._args = [title, message]

class NotificationFlashEvent(NotificationPopupEvent):
    """Emmited when a flash on the web front-end should occur."""

class NotificationSoundEvent(DelugeEvent):
    """Emitted when a sound notification is required"""
    def __init__(self, sound_path=""):
        """
        :param sound_path: the path to the notification sound
        :type title: string
        """
        self._args = [sound_path]
