import tempfile
import os
import signal

import common

from twisted.trial import unittest

from deluge.ui.client import client

# Start a daemon to test with and wait a couple seconds to make sure it's started
client.start_daemon(58847, config_directory)
import time
time.sleep(2)


class ClientTestCase(unittest.TestCase):
    def test_connect_no_credentials(self):
        d = client.connect("localhost", 58847)
        d.addCallback(self.assertEquals, 10)

        def on_connect(result):
            self.addCleanup(client.disconnect)
            return result
        d.addCallback(on_connect)
        return d
