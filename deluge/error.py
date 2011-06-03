#
# error.py
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
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


class DelugeError(Exception):
    def _get_message(self):
        return self._message
    def _set_message(self, message):
        self._message = message
    message = property(_get_message, _set_message)
    del _get_message, _set_message

    def __str__(self):
        return self.message

    def __new__(cls, *args, **kwargs):
        inst = super(DelugeError, cls).__new__(cls, *args, **kwargs)
        inst._args = args
        inst._kwargs = kwargs
        return inst

class NoCoreError(DelugeError):
    pass

class DaemonRunningError(DelugeError):
    pass

class InvalidTorrentError(DelugeError):
    pass

class InvalidPathError(DelugeError):
    pass

class _ClientSideRecreateError(DelugeError):
    pass

class IncompatibleClient(_ClientSideRecreateError):
    def __init__(self, daemon_version):
        self.daemon_version = daemon_version
        self.message = _(
            "Your deluge client is not compatible with the daemon. "
            "Please upgrade your client to %(daemon_version)s"
        ) % dict(daemon_version=self.daemon_version)

class NotAuthorizedError(_ClientSideRecreateError):

    def __init__(self, current_level, required_level):
        self.message = _(
            "Auth level too low: %(current_level)s < %(required_level)s" %
            dict(current_level=current_level, required_level=required_level)
        )
        self.current_level = current_level
        self.required_level = required_level


class _UsernameBasedPasstroughError(_ClientSideRecreateError):

    def _get_username(self):
        return self._username
    def _set_username(self, username):
        self._username = username
    username = property(_get_username, _set_username)
    del _get_username, _set_username

    def __init__(self, message, username):
        super(_UsernameBasedPasstroughError, self).__init__(message)
        self.message = message
        self.username = username


class BadLoginError(_UsernameBasedPasstroughError):
    pass

class AuthenticationRequired(_UsernameBasedPasstroughError):
    pass

class AuthManagerError(_UsernameBasedPasstroughError):
    pass
