#
# authmanager.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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

import os
import random
import stat
import shutil
import logging

import deluge.component as component
import deluge.configmanager as configmanager
from deluge.common import (AUTH_LEVEL_ADMIN, AUTH_LEVEL_NONE, AUTH_LEVEL_NORMAL,
                           AUTH_LEVEL_READONLY, AUTH_LEVEL_DEFAULT,
                           create_localclient_account)

from deluge.error import AuthManagerError, AuthenticationRequired, BadLoginError

log = logging.getLogger(__name__)

AUTH_LEVELS_MAPPING = {
    'NONE': AUTH_LEVEL_NONE,
    'READONLY': AUTH_LEVEL_READONLY,
    'DEFAULT': AUTH_LEVEL_NORMAL,
    'NORMAL': AUTH_LEVEL_DEFAULT,
    'ADMIN': AUTH_LEVEL_ADMIN
}

AUTH_LEVELS_MAPPING_REVERSE = {}
for key, value in AUTH_LEVELS_MAPPING.iteritems():
    AUTH_LEVELS_MAPPING_REVERSE[value] = key

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
            'authlevel_int': self.authlevel
        }

    def __repr__(self):
        return ('<Account username="%(username)s" authlevel=%(authlevel)s>' %
                self.__dict__)


class AuthManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, "AuthManager", interval=10)
        self.__auth = {}
        self.__auth_modification_time = None

    def start(self):
        self.__load_auth_file()

    def stop(self):
        self.__auth = {}

    def shutdown(self):
        pass

    def update(self):
        auth_file = configmanager.get_config_dir("auth")
        # Check for auth file and create if necessary
        if not os.path.exists(auth_file):
            log.info("Authfile not found, recreating it.")
            self.__load_auth_file()
            return

        auth_file_modification_time = os.stat(auth_file).st_mtime
        if self.__auth_modification_time != auth_file_modification_time:
            log.info("Auth file changed, reloading it!")
            self.__load_auth_file()

    def authorize(self, username, password):
        """
        Authorizes users based on username and password

        :param username: str, username
        :param password: str, password
        :returns: int, the auth level for this user
        :rtype: int

        :raises AuthenticationRequired: if aditional details are required to
                                        authenticate.
        :raises BadLoginError: if the username does not exist or password does
                               not match.

        """
        if not username:
            raise AuthenticationRequired(
                "Username and Password are required.", username
            )

        if username not in self.__auth:
            # Let's try to re-load the file.. Maybe it's been updated
            self.__load_auth_file()
            if username not in self.__auth:
                raise BadLoginError("Username does not exist", username)

        if self.__auth[username].password == password:
            # Return the users auth level
            return self.__auth[username].authlevel
        elif not password and self.__auth[username].password:
            raise AuthenticationRequired("Password is required", username)
        else:
            raise BadLoginError("Password does not match", username)

    def has_account(self, username):
        return username in self.__auth

    def get_known_accounts(self):
        """
        Returns a list of known deluge usernames.
        """
        self.__load_auth_file()
        return [account.data() for account in self.__auth.values()]

    def create_account(self, username, password, authlevel):
        if username in self.__auth:
            raise AuthManagerError("Username in use.", username)
        try:
            self.__auth[username] = Account(username, password,
                                            AUTH_LEVELS_MAPPING[authlevel])
            self.write_auth_file()
            return True
        except Exception, err:
            log.exception(err)
            raise err

    def update_account(self, username, password, authlevel):
        if username not in self.__auth:
            raise AuthManagerError("Username not known", username)
        try:
            self.__auth[username].username = username
            self.__auth[username].password = password
            self.__auth[username].authlevel = AUTH_LEVELS_MAPPING[authlevel]
            self.write_auth_file()
            return True
        except Exception, err:
            log.exception(err)
            raise err

    def remove_account(self, username):
        if username not in self.__auth:
            raise AuthManagerError("Username not known", username)
        elif username == component.get("RPCServer").get_session_user():
            raise AuthManagerError(
                "You cannot delete your own account while logged in!", username
            )

        del self.__auth[username]
        self.write_auth_file()
        return True

    def write_auth_file(self):
        old_auth_file = configmanager.get_config_dir("auth")
        new_auth_file = old_auth_file + '.new'
        bak_auth_file = old_auth_file + '.bak'
        # Let's first create a backup
        if os.path.exists(old_auth_file):
            shutil.copy2(old_auth_file, bak_auth_file)

        try:
            fd = open(new_auth_file, "w")
            for account in self.__auth.values():
                fd.write(
                    "%(username)s:%(password)s:%(authlevel_int)s\n" %
                    account.data()
                )
            fd.flush()
            os.fsync(fd.fileno())
            fd.close()
            os.rename(new_auth_file, old_auth_file)
        except:
            # Something failed, let's restore the previous file
            if os.path.exists(bak_auth_file):
                os.rename(bak_auth_file, old_auth_file)

        self.__load_auth_file()

    def __load_auth_file(self):
        save_and_reload = False
        auth_file = configmanager.get_config_dir("auth")
        # Check for auth file and create if necessary
        if not os.path.exists(auth_file):
            create_localclient_account()
            return self.__load_auth_file()

        auth_file_modification_time = os.stat(auth_file).st_mtime
        if self.__auth_modification_time is None:
            self.__auth_modification_time = auth_file_modification_time
        elif self.__auth_modification_time == auth_file_modification_time:
            # File didn't change, no need for re-parsing's
            return

        # Load the auth file into a dictionary: {username: Account(...)}
        f = open(auth_file, "r").readlines()

        for line in f:
            if line.startswith("#"):
                # This is a comment line
                continue
            line = line.strip()
            try:
                lsplit = line.split(":")
            except Exception, e:
                log.error("Your auth file is malformed: %s", e)
                continue
            if len(lsplit) == 2:
                username, password = lsplit
                log.warning("Your auth entry for %s contains no auth level, "
                            "using AUTH_LEVEL_DEFAULT(%s)..", username,
                            AUTH_LEVEL_DEFAULT)
                if username == 'localclient':
                    authlevel = AUTH_LEVEL_ADMIN
                else:
                    authlevel = AUTH_LEVEL_DEFAULT
                # This is probably an old auth file
                save_and_reload = True
            elif len(lsplit) == 3:
                username, password, authlevel = lsplit
            else:
                log.error("Your auth file is malformed: "
                          "Incorrect number of fields!")
                continue

            username = username.strip()
            password = password.strip()
            try:
                authlevel = int(authlevel)
            except ValueError:
                try:
                    authlevel = AUTH_LEVELS_MAPPING[authlevel]
                except KeyError:
                    log.error("Your auth file is malformed: %r is not a valid auth "
                              "level" % authlevel)
                continue

            self.__auth[username] = Account(username, password, authlevel)

        if "localclient" not in self.__auth:
            create_localclient_account(True)
            return self.__load_auth_file()


        if save_and_reload:
            log.info("Re-writing auth file (upgrade)")
            self.write_auth_file()
        self.__auth_modification_time = auth_file_modification_time

