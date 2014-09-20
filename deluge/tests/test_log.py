import logging

from twisted.internet import defer
from twisted.trial import unittest

from deluge.log import setup_logger


class LogTestCase(unittest.TestCase):
    def setUp(self):  # NOQA
        setup_logger(logging.DEBUG)

    def tearDown(self):  # NOQA
        setup_logger("none")

    def test_old_log_deprecation_warning(self):
        import warnings
        from deluge.log import LOG
        warnings.filterwarnings("ignore", category=DeprecationWarning,
                                module="deluge.tests.test_log")
        d = defer.Deferred()
        d.addCallback(LOG.debug, "foo")
        self.assertFailure(d, DeprecationWarning)
        warnings.resetwarnings()
