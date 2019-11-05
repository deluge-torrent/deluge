# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import hashlib
import logging
import os
import time
from datetime import datetime, timedelta
from email.utils import formatdate

from twisted.internet.task import LoopingCall

from deluge.common import AUTH_LEVEL_ADMIN, AUTH_LEVEL_NONE
from deluge.error import NotAuthorizedError
from deluge.ui.web.json_api import JSONComponent, WebapiNamespace

log = logging.getLogger(__name__)


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


auth_ns = WebapiNamespace('AUTH')


class AuthException(Exception):
    pass


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
        now = time.gmtime()
        for session_id in list(self.config['sessions']):
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

        Args:
            request (twisted.web.http.Request): The request
            login (str): the username of the user logging in, currently \
                         only for future use.

        Returns:
            bool: True of successfully created sessions

        Raises:
            AuthException: If request api base path is invalid

        """
        m = hashlib.sha256()
        m.update(os.urandom(32))
        session_id = m.hexdigest()

        expires, expires_str = make_expires(self.config['session_timeout'])
        checksum = str(make_checksum(session_id))

        # Is this necessary?
        # Ensure session_id is only valid for paths 'json' and 'api'
        api_base = request.path.decode()[len(request.base.decode()) :].split('/')[0]
        if api_base not in ['json', 'api']:
            raise AuthException('Invalid request base path: %s' % (api_base))

        request.addCookie(
            b'_session_id',
            session_id + checksum,
            path=request.base + api_base.encode(),
            expires=expires_str,
        )

        log.debug('Creating session for %s', login)

        if isinstance(self.config['sessions'], list):
            self.config['sessions'] = {}

        self.config['sessions'][session_id] = {
            'login': login,
            'level': AUTH_LEVEL_ADMIN,
            'expires': expires,
        }
        return True

    def check_password(self, password):
        config = self.config
        if 'pwd_sha1' not in config.config:
            log.debug('Failed to find config login details.')
            return False

        s = hashlib.sha1()
        s.update(config['pwd_salt'].encode('utf8'))
        s.update(password.encode('utf8'))
        return s.hexdigest() == config['pwd_sha1']

    def check_request(self, request, method=None, level=None):
        """
        Check to ensure that a request is authorised to call the specified
        method of authentication level.

        Args:
            request (twisted.web.http.Request): The HTTP request in question
            method (func): Check the specified method
            level (integer): Check the specified auth level

        Raises:
            AuthException:
            NotAuthorizedError: If user is not authorized

        """
        cookie_sess_id = request.getCookie(b'_session_id')
        if cookie_sess_id:
            session_id = get_session_id(cookie_sess_id.decode())
        else:
            session_id = None

        if session_id not in self.config['sessions']:
            auth_level = AUTH_LEVEL_NONE
            session_id = None
        else:
            session = self.config['sessions'][session_id]
            auth_level = session['level']
            expires, expires_str = make_expires(self.config['session_timeout'])
            session['expires'] = expires

            _session_id = request.getCookie(b'_session_id')
            request.addCookie(
                b'_session_id',
                _session_id,
                path=request.base + b'json',
                expires=expires_str.encode('utf8'),
            )

        if method:
            if not hasattr(method, '_json_export'):
                raise AuthException('Not an exported method')

            method_level = getattr(method, '_json_auth_level')
            if method_level is None:
                raise AuthException('Method has no auth level')

            level = method_level

        if level is None:
            raise AuthException('No level specified to check against')

        request.auth_level = auth_level
        request.session_id = session_id

        if auth_level < level:
            raise NotAuthorizedError(auth_level, level)

    def _change_password(self, new_password):
        """
        Change the password. This is to allow the UI to change/reset a
        password.

        Args:
            new_password (str): the password to change to

        """
        log.debug('Changing password')
        salt = hashlib.sha1(os.urandom(32)).hexdigest()
        s = hashlib.sha1(salt.encode('utf-8'))
        s.update(new_password.encode('utf8'))
        self.config['pwd_salt'] = salt
        self.config['pwd_sha1'] = s.hexdigest()
        return True

    @auth_ns.post
    def change_password(self, old_password, new_password):
        """
        Change the password.

        Args:
            old_password (str): the current password
            new_password (str): the password to change to

        Returns:
            bool: True if successfully changed the password, else False Example:: True

        """
        if not self.check_password(old_password):
            return False
        return self._change_password(new_password)

    @auth_ns.get(auth_level=AUTH_LEVEL_NONE)
    def check_session(self, session_id=None):
        """
        Check a session to see if it's still valid.

        Returns:
            bool: True if the session is valid, False if not Example:: True

        """
        return __request__.session_id is not None

    @auth_ns.get
    def delete_session(self):
        """
        Removes current a session.

        Returns:
            bool: True Example:: True

        """
        del self.config['sessions'][__request__.session_id]
        return True

    @auth_ns.post(auth_level=AUTH_LEVEL_NONE, password='deluge')
    def login(self, password):
        """
        Generate a session id and return it as a cookie

        Args:
            password (str): the password used to log in Example:: 'deluge'

        Returns:
            bool: True on successfull login else False Example:: True

        """
        if self.check_password(password):
            log.info('Login success (ClientIP %s)', __request__.getClientIP())
            return self._create_session(__request__)
        else:
            log.error('Login failed (ClientIP %s)', __request__.getClientIP())
            return False
