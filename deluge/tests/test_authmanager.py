#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os

import pytest

import deluge.component as component
from deluge.common import (
    AUTH_LEVEL_ADMIN,
    AUTH_LEVEL_NORMAL,
    get_localhost_auth,
)
from deluge.configmanager import get_config_dir
from deluge.conftest import BaseTestCase
from deluge.core.authmanager import AuthManager
from deluge.core.rpcserver import RPCServer
from deluge.error import AuthenticationRequired, BadLoginError


@pytest.fixture
def add_user_to_authfile():
    """Add user directly to the auth file."""

    def _add_user(username, password, level):
        auth_file = get_config_dir('auth')
        with open(auth_file, 'a') as file:
            file.write(f'{username}:{password}:{level}\n')

        # Force mtime to workaround Windows not updating for check by __load_auth_file.
        stat = os.stat(auth_file)
        os.utime(auth_file, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1000))

    return _add_user


class TestAuthManager(BaseTestCase):
    def set_up(self):
        self.auth = AuthManager()
        self.rpcserver = RPCServer(listen=False)
        self.auth.start()

    def tear_down(self):
        # We must ensure that the components in component registry are removed
        return component.shutdown()

    def test_authorize_localhost(self):
        username, password = get_localhost_auth()
        assert username == 'localclient'
        assert password
        assert self.auth.authorize(username, password) == AUTH_LEVEL_ADMIN

    @pytest.mark.parametrize('username', ['', None])
    def test_authorize_no_username_raises(self, username):
        with pytest.raises(AuthenticationRequired):
            self.auth.authorize(username, 'password')

    def test_authorize_no_password_raises(self):
        with pytest.raises(AuthenticationRequired):
            self.auth.authorize('localclient', '')

    def test_authorize_incorrect_username_raises(self):
        with pytest.raises(BadLoginError):
            self.auth.authorize('notuser', 'password')

    def test_authorize_wrong_password_raises(self):
        username, password = get_localhost_auth()
        assert username == 'localclient'
        assert password
        with pytest.raises(BadLoginError):
            self.auth.authorize(username, password + 'x')

    def test_create_account(self):
        self.auth.create_account('test', 'testpass', 'ADMIN')
        assert self.auth.has_account('test')
        assert self.auth.authorize('test', 'testpass') == AUTH_LEVEL_ADMIN

    def test_remove_account(self):
        self.auth.create_account('test', 'testpass', 'ADMIN')
        assert self.auth.has_account('test')

        self.auth.remove_account('test')
        assert not self.auth.has_account('test')

    def test_update_account(self):
        self.auth.create_account('test', 'testpass', 'ADMIN')
        assert self.auth.has_account('test')

        self.auth.update_account('test', 'testpass', 'NORMAL')
        assert self.auth.authorize('test', 'testpass') == AUTH_LEVEL_NORMAL

        self.auth.update_account('test', 'newpass', 'ADMIN')
        assert self.auth.authorize('test', 'newpass') == AUTH_LEVEL_ADMIN

    @pytest.mark.parametrize('password', ['testpass', '$testpa$$', 'test:pass'])
    def test_password_hashed(self, password):
        """Test account password is hashed with scrypt method."""
        self.auth.create_account('test', password, 'ADMIN')

        with open(get_config_dir('auth')) as file:
            user, result_password, _ = file.readlines()[1].strip().split(':')

        assert user == 'test'
        assert result_password.startswith('$scrypt$')
        assert password not in result_password

    @pytest.mark.parametrize('password', ['testpass1', '$testpa$$'])
    def test_password_plaintext(self, password, add_user_to_authfile):
        """Test account plaintext password is still accepted."""
        add_user_to_authfile('test', password, AUTH_LEVEL_ADMIN)

        assert self.auth.authorize('test', password) == AUTH_LEVEL_ADMIN

    def test_load_auth_level_str(self, add_user_to_authfile):
        """Test load auth config with auth level as string."""
        add_user_to_authfile('test', 'testpass', 'NORMAL')

        assert self.auth.authorize('test', 'testpass') == AUTH_LEVEL_NORMAL
