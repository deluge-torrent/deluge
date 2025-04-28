#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import pytest
import pytest_twisted
from twisted.internet import defer

from deluge import error
from deluge.common import AUTH_LEVEL_NORMAL, get_localhost_auth, get_version
from deluge.core.authmanager import AUTH_LEVEL_ADMIN
from deluge.ui.client import Client, DaemonSSLProxy, client


class NoVersionSendingDaemonSSLProxy(DaemonSSLProxy):
    def authenticate(self, username, password):
        self.login_deferred = defer.Deferred()
        d = self.call('daemon.login', username, password)
        d.addCallback(self.__on_login, username)
        d.addErrback(self.__on_login_fail)
        return self.login_deferred

    def __on_login(self, result, username):
        self.login_deferred.callback(result)

    def __on_login_fail(self, result):
        self.login_deferred.errback(result)


class NoVersionSendingClient(Client):
    def connect(
        self,
        host='127.0.0.1',
        port=58846,
        username='',
        password='',
        skip_authentication=False,
    ):
        self._daemon_proxy = NoVersionSendingDaemonSSLProxy()
        self._daemon_proxy.set_disconnect_callback(self.__on_disconnect)

        d = self._daemon_proxy.connect(host, port)

        def on_connect_fail(reason):
            self.disconnect()
            return reason

        def on_authenticate(result, daemon_info):
            return result

        def on_authenticate_fail(reason):
            return reason

        def on_connected(daemon_version):
            return daemon_version

        def authenticate(daemon_version, username, password):
            d = self._daemon_proxy.authenticate(username, password)
            d.addCallback(on_authenticate, daemon_version)
            d.addErrback(on_authenticate_fail)
            return d

        d.addCallback(on_connected)
        d.addErrback(on_connect_fail)
        if not skip_authentication:
            d.addCallback(authenticate, username, password)
        return d

    def __on_disconnect(self):
        if self.disconnect_callback:
            self.disconnect_callback()


@pytest.mark.usefixtures('daemon', 'client')
class TestClient:
    def test_connect_no_credentials(self):
        d = client.connect('localhost', self.listen_port, username='', password='')

        def on_connect(result):
            assert client.get_auth_level() == AUTH_LEVEL_ADMIN
            return result

        d.addCallbacks(on_connect, self.fail)
        return d

    def test_connect_localclient(self):
        username, password = get_localhost_auth()
        d = client.connect(
            'localhost', self.listen_port, username=username, password=password
        )

        def on_connect(result):
            assert client.get_auth_level() == AUTH_LEVEL_ADMIN
            return result

        d.addCallbacks(on_connect, self.fail)
        return d

    def test_connect_bad_password(self):
        username, password = get_localhost_auth()
        d = client.connect(
            'localhost', self.listen_port, username=username, password=password + '1'
        )

        def on_failure(failure):
            assert failure.trap(error.BadLoginError) == error.BadLoginError
            assert failure.value.message == 'Password does not match'

        d.addCallbacks(self.fail, on_failure)
        return d

    def test_connect_invalid_user(self):
        d = client.connect('localhost', self.listen_port, username='invalid-user')

        def on_failure(failure):
            assert failure.trap(error.BadLoginError) == error.BadLoginError
            assert failure.value.message == 'Username does not exist'

        d.addCallbacks(self.fail, on_failure)
        return d

    def test_connect_without_password(self):
        username, password = get_localhost_auth()
        d = client.connect('localhost', self.listen_port, username=username)

        def on_failure(failure):
            assert (
                failure.trap(error.AuthenticationRequired)
                == error.AuthenticationRequired
            )
            assert failure.value.username == username

        d.addCallbacks(self.fail, on_failure)
        return d

    @pytest_twisted.inlineCallbacks
    def test_connect_with_password(self):
        username, password = get_localhost_auth()
        yield client.connect(
            'localhost', self.listen_port, username=username, password=password
        )
        yield client.core.create_account('testuser', 'testpw', 'DEFAULT')
        yield client.disconnect()
        ret = yield client.connect(
            'localhost', self.listen_port, username='testuser', password='testpw'
        )
        assert ret == AUTH_LEVEL_NORMAL

    @pytest_twisted.inlineCallbacks
    def test_invalid_rpc_method_call(self):
        yield client.connect('localhost', self.listen_port, username='', password='')
        d = client.core.invalid_method()

        def on_failure(failure):
            assert failure.trap(error.WrappedException) == error.WrappedException

        d.addCallbacks(self.fail, on_failure)
        yield d

    def test_connect_without_sending_client_version_fails(self):
        username, password = get_localhost_auth()
        no_version_sending_client = NoVersionSendingClient()
        d = no_version_sending_client.connect(
            'localhost', self.listen_port, username=username, password=password
        )

        def on_failure(failure):
            assert failure.trap(error.IncompatibleClient) == error.IncompatibleClient

        d.addCallbacks(self.fail, on_failure)
        return d

    @pytest_twisted.inlineCallbacks
    def test_daemon_version(self):
        username, password = get_localhost_auth()
        yield client.connect(
            'localhost', self.listen_port, username=username, password=password
        )

        assert client.daemon_version == get_version()

    @pytest_twisted.inlineCallbacks
    def test_daemon_version_check_min(self):
        username, password = get_localhost_auth()
        yield client.connect(
            'localhost', self.listen_port, username=username, password=password
        )

        assert client.daemon_version_check_min(get_version())
        assert not client.daemon_version_check_min(f'{get_version()}1')
        assert client.daemon_version_check_min('0.1.0')
