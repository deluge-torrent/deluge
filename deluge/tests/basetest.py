import warnings

from twisted.internet.defer import maybeDeferred
from twisted.trial import unittest

import deluge.component as component


class BaseTestCase(unittest.TestCase):
    """This is the base class that should be used for all test classes
    that create classes that inherit from deluge.component.Component. It
    ensures that the component registry has been cleaned up when tests
    have finished.

    """
    def setUp(self):  # NOQA

        if len(component._ComponentRegistry.components) != 0:
            warnings.warn("The component._ComponentRegistry.components is not empty on test setup.\n"
                          "This is probably caused by another test that didn't clean up after finishing!: %s" %
                          component._ComponentRegistry.components)
        d = maybeDeferred(self.set_up)

        def on_setup_error(error):
            warnings.warn("Error caught in test setup!\n%s" % error.getTraceback())
            self.fail()

        return d.addErrback(on_setup_error)

    def tearDown(self):  # NOQA
        d = maybeDeferred(self.tear_down)

        def on_teardown_failed(error):
            warnings.warn("Error caught in test teardown!\n%s" % error.getTraceback())
            self.fail()

        def on_teardown_complete(result):
            component._ComponentRegistry.components.clear()
            component._ComponentRegistry.dependents.clear()

        return d.addCallbacks(on_teardown_complete, on_teardown_failed)

    def set_up(self):
        pass

    def tear_down(self):
        pass
