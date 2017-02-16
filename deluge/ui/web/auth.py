# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import hashlib
import logging
import os
import time
from datetime import datetime, timedelta
from email.utils import formatdate

from twisted.internet.task import LoopingCall

from deluge.common import utf8_encoded

log = logging.getLogger(__name__)


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

# Import after as json_api imports the above AuthError and AUTH_LEVEL_DEFAULT
from deluge.ui.web.json_api import export, JSONComponent  # NOQA, isort:skip pylint: disable=wrong-import-position


def make_checksum(session_id):
    checksum = 0
    for value in [ord(char) for char in session_id]:
        checksum += value
    return checksum


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
    except Exception as ex:
        log.exception(ex)
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

    def __init__(self, config):
        super(Auth, self).__init__('Auth')
        self.worker = LoopingCall(self._clean_sessions)
        self.config = config

    def start(self):
        self.worker.start(5)

    def stop(self):
        self.worker.stop()

    def _clean_sessions(self):
        session_ids = self.config['sessions'].keys()

        now = time.gmtime()
        for session_id in session_ids:
            session = self.config['sessions'][session_id]

            if 'expires' not in session:
                del self.config['sessions'][session_id]
                continue

            if time.gmtime(session['expires']) < now:
                del self.config['sessions'][session_id]
                continue

    def _create_session(self, request, login='admin'):
        """
        Creates a new session.

        :param login: the username of the user logging in, currently \
        only for future use currently.
        :type login: string
        """
        m = hashlib.sha256()
        m.update(os.urandom(32))
        session_id = m.hexdigest()

        expires, expires_str = make_expires(self.config['session_timeout'])
        checksum = str(make_checksum(session_id))

        request.addCookie('_session_id', session_id + checksum,
                          path=request.base + 'json', expires=expires_str)

        log.debug('Creating session for %s', login)

        if isinstance(self.config['sessions'], list):
            self.config['sessions'] = {}

        self.config['sessions'][session_id] = {
            'login': login,
            'level': AUTH_LEVEL_ADMIN,
            'expires': expires
        }
        return {'success': True, 'session_token': session_id + checksum}

    def check_password(self, password):
        config = self.config
        if 'pwd_md5' in config.config:
            # We are using the 1.2-dev auth method
            log.debug('Received a password via the 1.2-dev auth method')
            m = hashlib.md5()
            m.update(config['pwd_salt'])
            m.update(utf8_encoded(password))
            if m.hexdigest() == config['pwd_md5']:
                # We want to move the password over to sha1 and remove
                # the old passwords from the config file.
                self._change_password(password)
                del config.config['pwd_md5']

                # Remove the older password if there is now.
                if 'old_pwd_md5' in config.config:
                    del config.config['old_pwd_salt']
                    del config.config['old_pwd_md5']

                return True

        elif 'old_pwd_md5' in config.config:
            # We are using the 1.1 webui auth method
            log.debug('Received a password via the 1.1 auth method')
            from base64 import decodestring
            m = hashlib.md5()
            m.update(decodestring(config['old_pwd_salt']))
            m.update(utf8_encoded(password))
            if m.digest() == decodestring(config['old_pwd_md5']):

                # We want to move the password over to sha1 and remove
                # the old passwords from the config file.
                self._change_password(password)
                del config.config['old_pwd_salt']
                del config.config['old_pwd_md5']

                return True

        elif 'pwd_sha1' in config.config:
            # We are using the 1.2 auth method
            log.debug('Received a password via the 1.2 auth method')
            s = hashlib.sha1()
            s.update(config['pwd_salt'])
            s.update(utf8_encoded(password))
            if s.hexdigest() == config['pwd_sha1']:
                return True

        else:
            # Can't detect which method we should be using so just deny
            # access.
            log.debug('Failed to detect the login method')
            return False

    def _get_request_session_id(self, request):
        """Extract session ID from request.

        Extracts session ID from either X-Deluge-Session HTTP header, or
        _session_id cookie.

        Args:
            request (twisted.web.http.Request): The HTTP request in question
        Returns:
            string: The session ID.
            None: No session ID was sent with the request.
        """

        return request.getHeader('X-Deluge-Session') or request.getCookie('_session_id')

    def check_request(self, request, method=None, level=None):
        """
        Check to ensure that a request is authorised to call the specified
        method of authentication level.

        :param request: The HTTP request in question
        :type request: twisted.web.http.Request
        :param method: Check the specified method
        :type method: function
        :param level: Check the specified auth level
        :type level: integer

        :raises: Exception
        """

        session_id = get_session_id(self._get_request_session_id(request))

        if session_id not in self.config['sessions']:
            auth_level = AUTH_LEVEL_NONE
            session_id = None
        else:
            session = self.config['sessions'][session_id]
            auth_level = session['level']
            expires, expires_str = make_expires(self.config['session_timeout'])
            session['expires'] = expires

            _session_id = self._get_request_session_id(request)
            request.addCookie('_session_id', _session_id,
                              path=request.base + 'json', expires=expires_str)

        if method:
            if not hasattr(method, '_json_export'):
                raise Exception('Not an exported method')

            method_level = getattr(method, '_json_auth_level')
            if method_level is None:
                raise Exception('Method has no auth level')

            level = method_level

        if level is None:
            raise Exception('No level specified to check against')

        request.auth_level = auth_level
        request.session_id = session_id

        if auth_level < level:
            raise AuthError('Not authenticated')

    def _change_password(self, new_password):
        """
        Change the password. This is to allow the UI to change/reset a
        password.

        :param new_password: the password to change to
        :type new_password: string
        """
        log.debug('Changing password')
        salt = hashlib.sha1(os.urandom(32)).hexdigest()
        s = hashlib.sha1(salt)
        s.update(utf8_encoded(new_password))
        self.config['pwd_salt'] = salt
        self.config['pwd_sha1'] = s.hexdigest()
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
        del self.config['sessions'][__request__.session_id]
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
            return self._create_session(__request__)
        else:
            log.error('Login failed (ClientIP %s)', __request__.getClientIP())
            return False
