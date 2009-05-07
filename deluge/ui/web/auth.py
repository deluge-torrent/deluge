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
#   Boston, MA    02110-1301, USA.
#

AUTH_LEVEL_NONE = 0
AUTH_LEVEL_READONLY = 1
AUTH_LEVEL_NORMAL = 5
AUTH_LEVEL_ADMIN = 10

AUTH_LEVEL_DEFAULT = AUTH_LEVEL_NORMAL

import time
import random
import hashlib
import logging

from twisted.internet.defer import Deferred

from deluge import component
from deluge.ui.web.json_api import JSONComponent, export

log = logging.getLogger(__name__)

class Auth(JSONComponent):
    
    def __init__(self):
        super(Auth, self).__init__("Auth")
    
    def _create_session(self, login='admin'):
        """
        Creates a new session.
        
        :keyword login: str, the username of the user logging in, currently
        only for future use.
        """
        m = hashlib.md5()
        m.update(login)
        m.update(str(time.time()))
        m.update(str(random.getrandbits(40)))
        m.update(m.hexdigest())
        session_id = m.hexdigest()
        
        log.debug("Creating session for %s", login)
        config = component.get("DelugeWeb").config

        if type(config["sessions"]) is list:
            config.config["sessions"] = {}

        config["sessions"][session_id] = {
            "login": login
        }
        return session_id
    
    @export
    def change_password(self, new_password):
        """
        Change the password.
        
        :param new_password: str, the password to change to
        """
        log.debug("Changing password")
        d = Deferred()
        salt = hashlib.sha1(str(random.getrandbits(40))).hexdigest()
        s = hashlib.sha1(salt)
        s.update(new_password)
        config = component.get("DelugeWeb").config
        config["pwd_salt"] = salt
        config["pwd_sha1"] = s.hexdigest()
        d.callback(True)
        return d
        
    
    @export
    def check_session(self, session_id):
        """
        Check a session to see if it's still valid.
        
        :param session_id: str, the id for the session to remove
        :returns: True if the session is valid, False if not.
        :rtype: bool
        """
        d = Deferred()
        config = component.get("DelugeWeb").config
        d.callback(session_id in config["sessions"])
        return d
    
    @export
    def delete_session(self, session_id):
        """
        Removes a session.
        
        :param session_id: str, the id for the session to remove
        """
        d = Deferred()
        config = component.get("DelugeWeb").config
        del config["sessions"][session_id]
        d.callback(True)
        return d
    
    @export
    def login(self, password):
        """
        Test a password to see if it's valid.
        
        :param password: str, the password to test
        :returns: a session id or False
        """
        config = component.get("DelugeWeb").config
        d = Deferred()
        
        if "pwd_md5" in config.config:
            # We are using the 1.2-dev auth method
            log.debug("Received a login via the 1.2-dev auth method")
            m = hashlib.md5()
            m.update(config["pwd_salt"])
            m.update(password)
            if m.hexdigest() == config['pwd_md5']:
                # We have a match, so we can create and return a session id.
                d.callback(self._create_session())
                
                # We also want to move the password over to sha1 and remove
                # the old passwords from the config file.
                self.change_password(password)
                del config.config["pwd_md5"]
                
                # Remove the older password if there is now.
                if "old_pwd_md5" in config.config:
                    del config.config["old_pwd_salt"]
                    del config.config["old_pwd_md5"]
        
        elif "old_pwd_md5" in config.config:
            # We are using the 1.1 webui auth method
            log.debug("Received a login via the 1.1 auth method")
            from base64 import decodestring
            m = hashlib.md5()
            m.update(decodestring(config["old_pwd_salt"]))
            m.update(password)
            if m.digest() == decodestring(config["old_pwd_md5"]):
                # We have a match, so we can create and return a session id.
                d.callback(self._create_session())
                
                # We also want to move the password over to sha1 and remove
                # the old passwords from the config file.
                self.change_password(password)
                del config.config["old_pwd_salt"]
                del config.config["old_pwd_md5"]

        elif "pwd_sha1" in config.config:
            # We are using the 1.2 auth method
            log.debug("Received a login via the 1.2 auth method")
            s = hashlib.sha1()
            s.update(config["pwd_salt"])
            s.update(password)
            if s.hexdigest() == config["pwd_sha1"]:
                # We have a match, so we can create and return a session id.
                d.callback(self._create_session())

        else:
            # Can't detect which method we should be using so just deny
            # access.
            log.debug("Failed to detect the login method")
            d.callback(False)

        return d