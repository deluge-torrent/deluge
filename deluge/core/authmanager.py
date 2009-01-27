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
# 	Boston, MA    02110-1301, USA.
#

import os.path
import random
import stat

import deluge.component as component
import deluge.configmanager as configmanager

from deluge.log import LOG as log

AUTH_LEVEL_NONE = 0
AUTH_LEVEL_READONLY = 1
AUTH_LEVEL_NORMAL = 5
AUTH_LEVEL_ADMIN = 10

AUTH_LEVEL_DEFAULT = AUTH_LEVEL_NORMAL

class AuthManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, "AuthManager")
        self.__auth = {}

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
        :returns: int, the auth level for this user or 0 if not able to authenticate
        :rtype: int

        """

        if username not in self.__auth:
            # Let's try to re-load the file.. Maybe it's been updated
            self.__load_auth_file()
            if username not in self.__auth:
                return 0

        if self.__auth[username][0] == password:
            # Return the users auth level
            return self.__auth[username][1]

        return 0

    def __load_auth_file(self):
        auth_file = configmanager.get_config_dir("auth")
        # Check for auth file and create if necessary
        if not os.path.exists(auth_file):
            # We create a 'localclient' account with a random password
            try:
                from hashlib import sha1 as sha_hash
            except ImportError:
                from sha import new as sha_hash
            open(auth_file, "w").write("localclient:" + sha_hash(str(random.random())).hexdigest() + ":" + str(AUTH_LEVEL_ADMIN))
            # Change the permissions on the file so only this user can read/write it
            os.chmod(auth_file, stat.S_IREAD | stat.S_IWRITE)

        # Load the auth file into a dictionary: {username: password, ...}
        f = open(auth_file, "r")
        for line in f:
            if line.startswith("#"):
                # This is a comment line
                continue
            try:
                lsplit = line.split(":")
            except Exception, e:
                log.error("Your auth file is malformed: %s", e)
                continue
            if len(lsplit) == 2:
                username, password = lsplit
                log.warning("Your auth entry for %s contains no auth level, using AUTH_LEVEL_DEFAULT(%s)..", username, AUTH_LEVEL_DEFAULT)
                level = AUTH_LEVEL_DEFAULT
            elif len(lsplit) == 3:
                username, password, level = lsplit
            else:
                log.error("Your auth file is malformed: Incorrect number of fields!")
                continue

            self.__auth[username.strip()] = (password.strip(), level)
