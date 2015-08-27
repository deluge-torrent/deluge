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
            warnings.warn("The component._ComponentRegistry.components is not empty on test setup."
                          "This is probably caused by another test that didn't clean up after finishing!: %s" %
                          component._ComponentRegistry.components)
        return self.set_up()

    def tearDown(self):  # NOQA
        d = maybeDeferred(self.tear_down)

        def on_teared_down(result):
            component._ComponentRegistry.components.clear()
            component._ComponentRegistry.dependents.clear()

        return d.addCallback(on_teared_down)

    def set_up(self):
        pass

    def tear_down(self):
        pass
