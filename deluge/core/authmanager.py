#
# authmanager.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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
import logging

import deluge.component as component
import deluge.configmanager as configmanager
from deluge.error import BadLoginError, AuthenticationRequired

log = logging.getLogger(__name__)

AUTH_LEVEL_NONE = 0
AUTH_LEVEL_READONLY = 1
AUTH_LEVEL_NORMAL = 5
AUTH_LEVEL_ADMIN = 10

AUTH_LEVEL_DEFAULT = AUTH_LEVEL_NORMAL

class Account(object):
    __slots__ = ('username', 'password', 'auth_level')
    def __init__(self, username, password, auth_level):
        self.username = username
        self.password = password
        self.auth_level = auth_level

    def data(self, include_private=True):
        rv = self.__dict__.copy()
        if not include_private:
            rv['password'] = ''
        return rv

    def __repr__(self):
        return ('<Account username="%(username)s" auth_level=%(auth_level)s>' %
                self.__dict__)


class AuthManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, "AuthManager")
        self.__auth = {}
        self.__auth_modification_time = None

    def start(self):
        self.__load_auth_file()

    def stop(self):
        self.__auth = {}

    def shutdown(self):
        pass

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

        self.__test_existing_account(username)

        if self.__auth[username].password == password:
            # Return the users auth level
            return self.__auth[username].auth_level
        elif not password and self.__auth[username].password:
            raise AuthenticationRequired("Password is required", username)
        else:
            raise BadLoginError("Password does not match")

    def get_known_accounts(self, include_private_data=False):
        """
        Returns a list of known deluge usernames.
        """
        self.__load_auth_file()
        rv = {}
        for account in self.__auth.items():
            rv[account.username] = account.data(include_private_data)
        return rv

    def create_account(self, username, password='', auth_level=AUTH_LEVEL_DEFAULT):
        if username in self.__auth:
            raise Something()
        self.__create_account(username, password, auth_level)

    def update_account(self, username, password='', auth_level=AUTH_LEVEL_DEFAULT):
        if username in self.__auth:
            raise Something()
        self.__create_account(username, password, auth_level)

    def remove_account(self, username):
        if username in self.__auth:
            raise Something()
        del self.__auth[username]
        self.write_auth_file()
        if component.get("RPCServer").get_session_user() == username:
            # Force a client logout by the server
            component.get("RPCServer").logout_current_session()

    def write_auth_file(self):
        old_auth_file = configmanager.get_config_dir("auth")
        new_auth_file = old_auth_file + '.new'
        fd = open(new_auth_file, "w")
        for account in self.__auth.items():
            fd.write(
                "%(username)s:%(password)s:%(auth_level)s\n" % account.__dict__
            )
        fd.flush()
        os.fsync(fd.fileno())
        fd.close()
        os.rename(new_auth_file, old_auth_file)
        self.__load_auth_file()

    def __add_account(self, username, password, auth_level):
        self.__auth[username] = Account(username, password, auth_level)
        self.write_auth_file()

    def __test_existing_account(self, username):
        if username not in self.__auth:
            # Let's try to re-load the file.. Maybe it's been updated
            self.__load_auth_file()
            if username not in self.__auth:
                raise BadLoginError("Username does not exist")
        return True

    def __create_localclient_account(self):
        """
        Returns the string.
        """
        # We create a 'localclient' account with a random password
        try:
            from hashlib import sha1 as sha_hash
        except ImportError:
            from sha import new as sha_hash
        self.__auth["localclient"] = Account(
            "localclient",
            sha_hash(str(random.random())).hexdigest(),
            AUTH_LEVEL_ADMIN
        )

    def __load_auth_file(self):
        auth_file = configmanager.get_config_dir("auth")
        # Check for auth file and create if necessary
        if not os.path.exists(auth_file):
            self.__create_auth_file()
            self.__create_localclient_account()
            self.write_auth_file()

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
                auth_level = AUTH_LEVEL_DEFAULT
            elif len(lsplit) == 3:
                username, password, auth_level = lsplit
            else:
                log.error("Your auth file is malformed: Incorrect number of fields!")
                continue

            username = username.strip()
            password = password.strip()
            try:
                auth_level = int(auth_level)
            except ValueError:
                log.error("Your auth file is malformed: %r is not a valid auth "
                          "level" % auth_level)
                continue

            self.__auth[username] = Account(username, password, auth_level)

        if "localclient" not in self.__auth:
            self.__create_localclient_account()
            self.write_auth_file()


    def __create_auth_file(self):
        auth_file = configmanager.get_config_dir("auth")
        # Check for auth file and create if necessary
        if not os.path.exists(auth_file):
            fd = open(auth_file, "w")
            fd.flush()
            os.fsync(fd.fileno())
            fd.close()
            # Change the permissions on the file so only this user can read/write it
            os.chmod(auth_file, stat.S_IREAD | stat.S_IWRITE)
