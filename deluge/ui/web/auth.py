#
# deluge/ui/web/auth.py
#
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
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA  02110-1301, USA.
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

AUTH_LEVEL_NONE = 0
AUTH_LEVEL_READONLY = 1
AUTH_LEVEL_NORMAL = 5
AUTH_LEVEL_ADMIN = 10

AUTH_LEVEL_DEFAULT = AUTH_LEVEL_NORMAL

class AuthError(Exception):
    """
    An exception that might be raised when checking a request for
    authentication.
    """
    pass

import time
import random
import hashlib
import logging
from datetime import datetime, timedelta
from email.utils import formatdate

from twisted.internet.defer import Deferred
from twisted.internet.task import LoopingCall

from deluge import component
from deluge.ui.web.json_api import JSONComponent, export
from deluge.common import utf8_encoded

log = logging.getLogger(__name__)


def make_checksum(session_id):
    return reduce(lambda x,y:x+y, map(ord, session_id))


def get_session_id(session_id):
    """
    Checks a session id against its checksum
    """
    if not session_id:
        return None

    try:
        checksum = int(session_id[-4:])
        session_id = session_id[:-4]

        if checksum == make_checksum(session_id):
            return session_id
        return None
    except Exception, e:
        log.exception(e)
        return None


def make_expires(timeout):
    dt = timedelta(seconds=timeout)
    expires = time.mktime((datetime.now() + dt).timetuple())
    expires_str = formatdate(timeval=expires, localtime=False, usegmt=True)
    return expires, expires_str


class Auth(JSONComponent):
    """
    The component that implements authentification into the JSON interface.
    """

    def __init__(self):
        super(Auth, self).__init__("Auth")
        self.worker = LoopingCall(self._clean_sessions)
        self.worker.start(5)

    def _clean_sessions(self):
        config = component.get("DelugeWeb").config
        session_ids = config["sessions"].keys()

        now = time.gmtime()
        for session_id in session_ids:
            session = config["sessions"][session_id]

            if "expires" not in session:
                del config["sessions"][session_id]
                continue

            if time.gmtime(session["expires"]) < now:
                del config["sessions"][session_id]
                continue

    def _create_session(self, request, login='admin'):
        """
        Creates a new session.

        :keyword login: the username of the user logging in, currently \
        only for future use currently.
        :type login: string
        """
        m = hashlib.md5()
        m.update(login)
        m.update(str(time.time()))
        m.update(str(random.getrandbits(40)))
        m.update(m.hexdigest())
        session_id = m.hexdigest()

        config = component.get("DelugeWeb").config

        expires, expires_str = make_expires(config["session_timeout"])
        checksum = str(make_checksum(session_id))

        request.addCookie('_session_id', session_id + checksum,
                path=request.base+"json", expires=expires_str)

        log.debug("Creating session for %s", login)
        config = component.get("DelugeWeb").config

        if type(config["sessions"]) is list:
            config.config["sessions"] = {}

        config["sessions"][session_id] = {
            "login": login,
            "level": AUTH_LEVEL_ADMIN,
            "expires": expires
        }
        return True

    def check_password(self, password):
        config = component.get("DelugeWeb").config
        if "pwd_md5" in config.config:
            # We are using the 1.2-dev auth method
            log.debug("Received a password via the 1.2-dev auth method")
            m = hashlib.md5()
            m.update(config["pwd_salt"])
            m.update(utf8_encoded(password))
            if m.hexdigest() == config['pwd_md5']:
                # We want to move the password over to sha1 and remove
                # the old passwords from the config file.
                self._change_password(password)
                del config.config["pwd_md5"]

                # Remove the older password if there is now.
                if "old_pwd_md5" in config.config:
                    del config.config["old_pwd_salt"]
                    del config.config["old_pwd_md5"]

                return True

        elif "old_pwd_md5" in config.config:
            # We are using the 1.1 webui auth method
            log.debug("Received a password via the 1.1 auth method")
            from base64 import decodestring
            m = hashlib.md5()
            m.update(decodestring(config["old_pwd_salt"]))
            m.update(utf8_encoded(password))
            if m.digest() == decodestring(config["old_pwd_md5"]):

                # We want to move the password over to sha1 and remove
                # the old passwords from the config file.
                self._change_password(password)
                del config.config["old_pwd_salt"]
                del config.config["old_pwd_md5"]

                return True

        elif "pwd_sha1" in config.config:
            # We are using the 1.2 auth method
            log.debug("Received a password via the 1.2 auth method")
            s = hashlib.sha1()
            s.update(config["pwd_salt"])
            s.update(utf8_encoded(password))
            if s.hexdigest() == config["pwd_sha1"]:
                return True

        else:
            # Can't detect which method we should be using so just deny
            # access.
            log.debug("Failed to detect the login method")
            return False

    def check_request(self, request, method=None, level=None):
        """
        Check to ensure that a request is authorised to call the specified
        method of authentication level.

        :param request: The HTTP request in question
        :type request: twisted.web.http.Request
        :keyword method: Check the specified method
        :type method: function
        :keyword level: Check the specified auth level
        :type level: integer

        :raises: Exception
        """

        config = component.get("DelugeWeb").config
        session_id = get_session_id(request.getCookie("_session_id"))

        if session_id not in config["sessions"]:
            auth_level = AUTH_LEVEL_NONE
            session_id = None
        else:
            session = config["sessions"][session_id]
            auth_level = session["level"]
            expires, expires_str = make_expires(config["session_timeout"])
            session["expires"] = expires

            _session_id = request.getCookie("_session_id")
            request.addCookie('_session_id', _session_id,
                    path=request.base+"json", expires=expires_str)

        if method:
            if not hasattr(method, "_json_export"):
                raise Exception("Not an exported method")

            method_level = getattr(method, "_json_auth_level")
            if method_level is None:
                raise Exception("Method has no auth level")

            level = method_level

        if level is None:
            raise Exception("No level specified to check against")

        request.auth_level = auth_level
        request.session_id = session_id

        if auth_level < level:
            raise AuthError("Not authenticated")

    def _change_password(self, new_password):
        """
        Change the password. This is to allow the UI to change/reset a
        password.

        :param new_password: the password to change to
        :type new_password: string
        """
        log.debug("Changing password")
        salt = hashlib.sha1(str(random.getrandbits(40))).hexdigest()
        s = hashlib.sha1(salt)
        s.update(utf8_encoded(new_password))
        config = component.get("DelugeWeb").config
        config["pwd_salt"] = salt
        config["pwd_sha1"] = s.hexdigest()
        return True

    @export
    def change_password(self, old_password, new_password):
        """
        Change the password.

        :param old_password: the current password
        :type old_password: string
        :param new_password: the password to change to
        :type new_password: string
        """
        if not self.check_password(old_password):
            return False
        return self._change_password(new_password)

    @export(AUTH_LEVEL_NONE)
    def check_session(self, session_id=None):
        """
        Check a session to see if it's still valid.

        :returns: True if the session is valid, False if not.
        :rtype: booleon
        """
        return __request__.session_id is not None

    @export
    def delete_session(self):
        """
        Removes a session.

        :param session_id: the id for the session to remove
        :type session_id: string
        """
        d = Deferred()
        config = component.get("DelugeWeb").config
        del config["sessions"][__request__.session_id]
        return True

    @export(AUTH_LEVEL_NONE)
    def login(self, password):
        """
        Test a password to see if it's valid.

        :param password: the password to test
        :type password: string
        :returns: a session id or False
        :rtype: string or False
        """
        if self.check_password(password):
            log.info('Login success (ClientIP %s)', __request__.getClientIP())
            return self._create_session(__request__)
        else:
            log.error('Login failed (ClientIP %s)', __request__.getClientIP())
            return False
