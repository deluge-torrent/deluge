#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
import subprocess
from pathlib import Path

import pytest
from twisted.internet import defer, protocol, reactor

import deluge.component as component
import deluge.ui.web.server
from deluge import configmanager
from deluge.common import windows_check
from deluge.conftest import BaseTestCase
from deluge.ui.web.server import DelugeWeb

from .common import get_test_data_file
from .common_web import WebServerTestBase
from .daemon_base import DaemonBase

SECURITY_TESTS = bool(os.getenv('SECURITY_TESTS', False))


class PrintingProcessProtocol(protocol.ProcessProtocol):
    """
    A ProcessProtocol that streams stdout and stderr directly to the console in real-time.

    This is used instead of getProcessOutputAndValue to provide immediate feedback during
    long-running security tests, making it easier to monitor progress and debug hangs.
    """

    def __init__(self, deferred):
        self.deferred = deferred
        self.out = b''
        self.err = b''

    def outReceived(self, data):  # noqa: N802
        self.out += data
        print(data.decode('utf-8', 'replace'), end='')

    def errReceived(self, data):  # noqa: N802
        self.err += data
        print(data.decode('utf-8', 'replace'), end='')

    def processEnded(self, reason):  # noqa: N802
        if reason.value.exitCode == 0:
            self.deferred.callback((self.out, self.err, 0))
        else:
            self.deferred.callback((self.out, self.err, reason.value.exitCode))


@pytest.fixture(scope='session')
def testssl_bin():
    testssl_dir = Path(get_test_data_file('testssl_repo')).absolute()
    testssl_sh = testssl_dir / 'testssl.sh'
    if not testssl_sh.exists():
        # Clone if missing
        subprocess.check_call(
            [
                'git',
                'clone',
                '--depth',
                '1',
                'https://github.com/drwetter/testssl.sh.git',
                str(testssl_dir),
            ]
        )
    return str(testssl_sh)


# TODO: This whole module has not been tested since migrating tests fully to pytest
class SecurityBaseTestCase:
    @pytest.fixture(autouse=True)
    def setvars(self, testssl_bin):
        self.port = 8112
        self.testssl_bin = testssl_bin

    def _run_test(self, test):
        d = defer.Deferred()
        proto = PrintingProcessProtocol(d)

        args = [
            self.testssl_bin,
            '--quiet',
            '--nodns',
            'none',
            '--color',
            '0',
            '--socket-timeout',
            '5',
            '--openssl-timeout',
            '5',
            test,
            '127.0.0.1:%d' % self.port,
        ]

        reactor.spawnProcess(proto, 'bash', ['bash'] + args)

        def on_result(results):
            if test == '-e':
                results = results[0].split(b'\n')[7:-6]
                assert len(results) > 3
            else:
                # Decode to string for easier filtering
                output = results[0].decode('utf-8', 'replace')

                # Filter out known non-critical failures for self-signed/dev certs
                lines = output.splitlines()
                lines = [
                    line
                    for line in lines
                    if 'Chain of trust' not in line
                    and 'Trust (hostname)' not in line
                    and 'OCSP URI' not in line
                ]
                filtered_output = '\n'.join(lines)

                assert 'OK' in filtered_output
                assert 'NOT ok' not in filtered_output

        d.addCallback(on_result)
        return d

    def test_secured_webserver_protocol(self):
        return self._run_test('-p')

    def test_secured_webserver_standard_ciphers(self):
        return self._run_test('-s')

    def test_secured_webserver_heartbleed_vulnerability(self):
        return self._run_test('-H')

    def test_secured_webserver_css_injection_vulnerability(self):
        return self._run_test('-I')

    def test_secured_webserver_renegotiation_vulnerabilities(self):
        return self._run_test('-R')

    def test_secured_webserver_crime_vulnerability(self):
        return self._run_test('-C')

    def test_secured_webserver_poodle_vulnerability(self):
        return self._run_test('-O')

    def test_secured_webserver_tls_fallback_scsv_mitigation_vulnerability(self):
        return self._run_test('-Z')

    def test_secured_webserver_sweet32_vulnerability(self):
        return self._run_test('-W')

    def test_secured_webserver_beast_vulnerability(self):
        return self._run_test('-A')

    def test_secured_webserver_lucky13_vulnerability(self):
        return self._run_test('-L')

    def test_secured_webserver_freak_vulnerability(self):
        return self._run_test('-F')

    def test_secured_webserver_logjam_vulnerability(self):
        return self._run_test('-J')

    def test_secured_webserver_drown_vulnerability(self):
        return self._run_test('-D')

    def test_secured_webserver_forward_secrecy_settings(self):
        return self._run_test('-f')

    def test_secured_webserver_rc4_ciphers(self):
        return self._run_test('--rc4')

    def test_secured_webserver_preference(self):
        return self._run_test('-P')

    def test_secured_webserver_ciphers(self):
        return self._run_test('-e')


@pytest.mark.skipif(windows_check(), reason='windows cannot run .sh files')
@pytest.mark.skipif(not SECURITY_TESTS, reason='skipping security tests')
@pytest.mark.security
class TestDaemonSecurity(BaseTestCase, DaemonBase, SecurityBaseTestCase):
    def set_up(self):
        d = self.common_set_up()
        self.port = self.listen_port
        d.addCallback(self.start_core)
        d.addErrback(self.terminate_core)
        return d

    def tear_down(self):
        d = component.shutdown()
        d.addCallback(self.terminate_core)
        return d


@pytest.mark.skipif(windows_check(), reason='windows cannot run .sh files')
@pytest.mark.skipif(not SECURITY_TESTS, reason='skipping security tests')
@pytest.mark.security
class TestWebUISecurity(WebServerTestBase, SecurityBaseTestCase):
    def start_webapi(self, arg):
        self.port = 8999

        config_defaults = deluge.ui.web.server.CONFIG_DEFAULTS.copy()
        config_defaults['port'] = self.port
        config_defaults['https'] = True
        self.config = configmanager.ConfigManager('web.conf', config_defaults)

        self.deluge_web = DelugeWeb(daemon=False)

        host = list(self.deluge_web.web_api.hostlist.config['hosts'][0])
        host[2] = self.listen_port
        self.deluge_web.web_api.hostlist.config['hosts'][0] = tuple(host)
        self.host_id = host[0]
        self.deluge_web.start()

    def test_secured_webserver_headers(self):
        return self._run_test('-h')

    def test_secured_webserver_breach_vulnerability(self):
        return self._run_test('-B')

    def test_secured_webserver_ticketbleed_vulnerability(self):
        return self._run_test('-T')
