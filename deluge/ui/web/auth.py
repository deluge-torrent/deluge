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

import time
import random
import hashlib
import logging

from twisted.internet.defer import Deferred

from deluge import component
from deluge.ui.web.json_api import JSONComponent, export

log = logging.getLogger(__name__)

class Auth(JSONComponent):
    """
    The component that implements authentification into the JSON interface.
    """
    
    def __init__(self):
        super(Auth, self).__init__("Auth")
    
    def _create_session(self, login='admin'):
        """
        Creates a new session.
        
        :keyword login: the username of the user logging in, currently \
        only for future use.
        :type login: string
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
        
        :param new_password: the password to change to
        :type new_password: string
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
        
        :param session_id: the id for the session to remove
        :type session_id: string
        :returns: True if the session is valid, False if not.
        :rtype: booleon
        """
        d = Deferred()
        config = component.get("DelugeWeb").config
        d.callback(session_id in config["sessions"])
        return d
    
    @export
    def delete_session(self, session_id):
        """
        Removes a session.
        
        :param session_id: the id for the session to remove
        :type session_id: string
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
        
        :param password: the password to test
        :type password: string
        :returns: a session id or False
        :rtype: string or False
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