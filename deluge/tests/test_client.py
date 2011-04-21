import os
import sys
import time
import signal
import tempfile

from subprocess import Popen, PIPE

import common

from twisted.trial import unittest

from deluge.ui.client import client

CWD = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

DAEMON_SCRIPT = """
import sys
import deluge.main

sys.argv.extend(['-d', '-c', '%s', '-Linfo'])

deluge.main.start_daemon()
"""

class ClientTestCase(unittest.TestCase):

    def setUp(self):
        config_directory = common.set_tmp_config_dir()

        fp = tempfile.TemporaryFile()
        fp.write(DAEMON_SCRIPT % config_directory)
        fp.seek(0)

        self.core = Popen([sys.executable], cwd=CWD,
                          stdin=fp, stdout=PIPE, stderr=PIPE)

        listening = False
        while not listening:
            line = self.core.stderr.readline()
            if "Factory starting on 58846" in line:
                listening = True
                time.sleep(0.1) # Slight pause just incase
                break


    def tearDown(self):
        self.core.terminate()

    def test_connect_no_credentials(self):
        d = client.connect("localhost", 58846)
        d.addCallback(self.assertEquals, 10)

        def on_connect(result):
            self.addCleanup(client.disconnect)
            return result

        d.addCallback(on_connect)
        return d
