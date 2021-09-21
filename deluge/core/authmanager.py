# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os
import shutil
from io import open

import deluge.component as component
import deluge.configmanager as configmanager
from deluge.common import (
    AUTH_LEVEL_ADMIN,
    AUTH_LEVEL_DEFAULT,
    AUTH_LEVEL_NONE,
    AUTH_LEVEL_NORMAL,
    AUTH_LEVEL_READONLY,
    create_localclient_account,
)
from deluge.error import AuthenticationRequired, AuthManagerError, BadLoginError

log = logging.getLogger(__name__)

AUTH_LEVELS_MAPPING = {
    'NONE': AUTH_LEVEL_NONE,
    'READONLY': AUTH_LEVEL_READONLY,
    'DEFAULT': AUTH_LEVEL_NORMAL,
    'NORMAL': AUTH_LEVEL_DEFAULT,
    'ADMIN': AUTH_LEVEL_ADMIN,
}
AUTH_LEVELS_MAPPING_REVERSE = {v: k for k, v in AUTH_LEVELS_MAPPING.items()}


class Account(object):
    __slots__ = ('username', 'password', 'authlevel')

    def __init__(self, username, password, authlevel):
        self.username = username
        self.password = password
        self.authlevel = authlevel

    def data(self):
        return {
            'username': self.username,
            'password': self.password,
            'authlevel': AUTH_LEVELS_MAPPING_REVERSE[self.authlevel],
            'authlevel_int': self.authlevel,
        }

    def __repr__(self):
        return '<Account username="%(username)s" authlevel=%(authlevel)s>' % {
            'username': self.username,
            'authlevel': self.authlevel,
        }


class AuthManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, 'AuthManager', interval=10)
        self.__auth = {}
        self.__auth_modification_time = None

    def start(self):
        self.__load_auth_file()

    def stop(self):
        self.__auth = {}

    def shutdown(self):
        pass

    def update(self):
        auth_file = configmanager.get_config_dir('auth')
        # Check for auth file and create if necessary
        if not os.path.isfile(auth_file):
            log.info('Authfile not found, recreating it.')
            self.__load_auth_file()
            return

        auth_file_modification_time = os.stat(auth_file).st_mtime
        if self.__auth_modification_time != auth_file_modification_time:
            log.info('Auth file changed, reloading it!')
            self.__load_auth_file()

    def authorize(self, username, password):
        """Authorizes users based on username and password.

        Args:
            username (str): Username
            password (str): Password

        Returns:
            int: The auth level for this user.

        Raises:
            AuthenticationRequired: If additional details are required to authenticate.
            BadLoginError: If the username does not exist or password does not match.

        """
        if not username:
            raise AuthenticationRequired(
                'Username and Password are required.', username
            )

        if username not in self.__auth:
            # Let's try to re-load the file.. Maybe it's been updated
            self.__load_auth_file()
            if username not in self.__auth:
                raise BadLoginError('Username does not exist', username)

        if self.__auth[username].password == password:
            # Return the users auth level
            return self.__auth[username].authlevel
        elif not password and self.__auth[username].password:
            raise AuthenticationRequired('Password is required', username)
        else:
            raise BadLoginError('Password does not match', username)

    def has_account(self, username):
        return username in self.__auth

    def get_known_accounts(self):
        """Returns a list of known deluge usernames."""
        self.__load_auth_file()
        return [account.data() for account in self.__auth.values()]

    def create_account(self, username, password, authlevel):
        if username in self.__auth:
            raise AuthManagerError('Username in use.', username)
        if authlevel not in AUTH_LEVELS_MAPPING:
            raise AuthManagerError('Invalid auth level: %s' % authlevel)
        try:
            self.__auth[username] = Account(
                username, password, AUTH_LEVELS_MAPPING[authlevel]
            )
            self.write_auth_file()
            return True
        except Exception as ex:
            log.exception(ex)
            raise ex

    def update_account(self, username, password, authlevel):
        if username not in self.__auth:
            raise AuthManagerError('Username not known', username)
        if authlevel not in AUTH_LEVELS_MAPPING:
            raise AuthManagerError('Invalid auth level: %s' % authlevel)
        try:
            self.__auth[username].username = username
            self.__auth[username].password = password
            self.__auth[username].authlevel = AUTH_LEVELS_MAPPING[authlevel]
            self.write_auth_file()
            return True
        except Exception as ex:
            log.exception(ex)
            raise ex

    def remove_account(self, username):
        if username not in self.__auth:
            raise AuthManagerError('Username not known', username)
        elif username == component.get('RPCServer').get_session_user():
            raise AuthManagerError(
                'You cannot delete your own account while logged in!', username
            )

        del self.__auth[username]
        self.write_auth_file()
        return True

    def write_auth_file(self):
        filename = 'auth'
        filepath = os.path.join(configmanager.get_config_dir(), filename)
        filepath_bak = filepath + '.bak'
        filepath_tmp = filepath + '.tmp'

        try:
            if os.path.isfile(filepath):
                log.debug('Creating backup of %s at: %s', filename, filepath_bak)
                shutil.copy2(filepath, filepath_bak)
        except IOError as ex:
            log.error('Unable to backup %s to %s: %s', filepath, filepath_bak, ex)
        else:
            log.info('Saving the %s at: %s', filename, filepath)
            try:
                with open(filepath_tmp, 'w', encoding='utf8') as _file:
                    for account in self.__auth.values():
                        _file.write(
                            '%(username)s:%(password)s:%(authlevel_int)s\n'
                            % account.data()
                        )
                    _file.flush()
                    os.fsync(_file.fileno())
                shutil.move(filepath_tmp, filepath)
            except IOError as ex:
                log.error('Unable to save %s: %s', filename, ex)
                if os.path.isfile(filepath_bak):
                    log.info('Restoring backup of %s from: %s', filename, filepath_bak)
                    shutil.move(filepath_bak, filepath)

        self.__load_auth_file()

    def __load_auth_file(self):
        save_and_reload = False
        filename = 'auth'
        auth_file = configmanager.get_config_dir(filename)
        auth_file_bak = auth_file + '.bak'

        # Check for auth file and create if necessary
        if not os.path.isfile(auth_file):
            create_localclient_account()
            return self.__load_auth_file()

        auth_file_modification_time = os.stat(auth_file).st_mtime
        if self.__auth_modification_time is None:
            self.__auth_modification_time = auth_file_modification_time
        elif self.__auth_modification_time == auth_file_modification_time:
            # File didn't change, no need for re-parsing's
            return

        for _filepath in (auth_file, auth_file_bak):
            log.info('Opening %s for load: %s', filename, _filepath)
            try:
                with open(_filepath, 'r', encoding='utf8') as _file:
                    file_data = _file.readlines()
            except IOError as ex:
                log.warning('Unable to load %s: %s', _filepath, ex)
                file_data = []
            else:
                log.info('Successfully loaded %s: %s', filename, _filepath)
                break

        # Load the auth file into a dictionary: {username: Account(...)}
        for line in file_data:
            line = line.strip()
            if line.startswith('#') or not line:
                # This line is a comment or empty
                continue
            lsplit = line.split(':')
            if len(lsplit) == 2:
                username, password = lsplit
                log.warning(
                    'Your auth entry for %s contains no auth level, '
                    'using AUTH_LEVEL_DEFAULT(%s)..',
                    username,
                    AUTH_LEVEL_DEFAULT,
                )
                if username == 'localclient':
                    authlevel = AUTH_LEVEL_ADMIN
                else:
                    authlevel = AUTH_LEVEL_DEFAULT
                # This is probably an old auth file
                save_and_reload = True
            elif len(lsplit) == 3:
                username, password, authlevel = lsplit
            else:
                log.error('Your auth file is malformed: Incorrect number of fields!')
                continue

            username = username.strip()
            password = password.strip()
            try:
                authlevel = int(authlevel)
            except ValueError:
                try:
                    authlevel = AUTH_LEVELS_MAPPING[authlevel]
                except KeyError:
                    log.error(
                        'Your auth file is malformed: %r is not a valid auth level',
                        authlevel,
                    )
                continue

            self.__auth[username] = Account(username, password, authlevel)

        if 'localclient' not in self.__auth:
            create_localclient_account(True)
            return self.__load_auth_file()

        if save_and_reload:
            log.info('Re-writing auth file (upgrade)')
            self.write_auth_file()
        self.__auth_modification_time = auth_file_modification_time
