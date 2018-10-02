# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from twisted.internet import defer, threads
from twisted.trial.unittest import SkipTest

import deluge.component as component

from .basetest import BaseTestCase


class ComponentTester(component.Component):
    def __init__(self, name, depend=None):
        component.Component.__init__(self, name, depend=depend)
        self.start_count = 0
        self.stop_count = 0

    def start(self):
        self.start_count += 1

    def stop(self):
        self.stop_count += 1


class ComponentTesterDelayStart(ComponentTester):
    def start(self):
        def do_sleep():
            import time

            time.sleep(1)

        d = threads.deferToThread(do_sleep)

        def on_done(result):
            self.start_count += 1

        return d.addCallback(on_done)


class ComponentTesterUpdate(component.Component):
    def __init__(self, name):
        component.Component.__init__(self, name)
        self.counter = 0
        self.start_count = 0
        self.stop_count = 0

    def update(self):
        self.counter += 1

    def stop(self):
        self.stop_count += 1


class ComponentTesterShutdown(component.Component):
    def __init__(self, name):
        component.Component.__init__(self, name)
        self.shutdowned = False
        self.stop_count = 0

    def shutdown(self):
        self.shutdowned = True

    def stop(self):
        self.stop_count += 1


class ComponentTestClass(BaseTestCase):
    def tear_down(self):
        return component.shutdown()

    def test_start_component(self):
        def on_start(result, c):
            self.assertEqual(c._component_state, 'Started')
            self.assertEqual(c.start_count, 1)

        c = ComponentTester('test_start_c1')
        d = component.start(['test_start_c1'])
        d.addCallback(on_start, c)
        return d

    def test_start_stop_depends(self):
        def on_stop(result, c1, c2):
            self.assertEqual(c1._component_state, 'Stopped')
            self.assertEqual(c2._component_state, 'Stopped')
            self.assertEqual(c1.stop_count, 1)
            self.assertEqual(c2.stop_count, 1)

        def on_start(result, c1, c2):
            self.assertEqual(c1._component_state, 'Started')
            self.assertEqual(c2._component_state, 'Started')
            self.assertEqual(c1.start_count, 1)
            self.assertEqual(c2.start_count, 1)
            return component.stop(['test_start_depends_c1']).addCallback(
                on_stop, c1, c2
            )

        c1 = ComponentTester('test_start_depends_c1')
        c2 = ComponentTester('test_start_depends_c2', depend=['test_start_depends_c1'])

        d = component.start(['test_start_depends_c2'])
        d.addCallback(on_start, c1, c2)
        return d

    def start_with_depends(self):
        c1 = ComponentTesterDelayStart('test_start_all_c1')
        c2 = ComponentTester('test_start_all_c2', depend=['test_start_all_c4'])
        c3 = ComponentTesterDelayStart(
            'test_start_all_c3', depend=['test_start_all_c5', 'test_start_all_c1']
        )
        c4 = ComponentTester('test_start_all_c4', depend=['test_start_all_c3'])
        c5 = ComponentTester('test_start_all_c5')

        d = component.start()
        return (d, c1, c2, c3, c4, c5)

    def finish_start_with_depends(self, *args):
        for c in args[1:]:
            component.deregister(c)

    def test_start_all(self):
        def on_start(*args):
            for c in args[1:]:
                self.assertEqual(c._component_state, 'Started')
                self.assertEqual(c.start_count, 1)

        ret = self.start_with_depends()
        ret[0].addCallback(on_start, *ret[1:])
        ret[0].addCallback(self.finish_start_with_depends, *ret[1:])
        return ret[0]

    def test_register_exception(self):
        ComponentTester('test_register_exception_c1')
        self.assertRaises(
            component.ComponentAlreadyRegistered,
            ComponentTester,
            'test_register_exception_c1',
        )

    def test_stop_component(self):
        def on_stop(result, c):
            self.assertEqual(c._component_state, 'Stopped')
            self.assertFalse(c._component_timer.running)
            self.assertEqual(c.stop_count, 1)

        def on_start(result, c):
            self.assertEqual(c._component_state, 'Started')
            return component.stop(['test_stop_component_c1']).addCallback(on_stop, c)

        c = ComponentTesterUpdate('test_stop_component_c1')
        d = component.start(['test_stop_component_c1'])
        d.addCallback(on_start, c)
        return d

    def test_stop_all(self):
        def on_stop(result, *args):
            for c in args:
                self.assertEqual(c._component_state, 'Stopped')
                self.assertEqual(c.stop_count, 1)

        def on_start(result, *args):
            for c in args:
                self.assertEqual(c._component_state, 'Started')
            return component.stop().addCallback(on_stop, *args)

        ret = self.start_with_depends()
        ret[0].addCallback(on_start, *ret[1:])
        ret[0].addCallback(self.finish_start_with_depends, *ret[1:])
        return ret[0]

    def test_update(self):
        def on_start(result, c1, counter):
            self.assertTrue(c1._component_timer)
            self.assertTrue(c1._component_timer.running)
            self.assertNotEqual(c1.counter, counter)
            return component.stop()

        c1 = ComponentTesterUpdate('test_update_c1')
        cnt = int(c1.counter)
        d = component.start(['test_update_c1'])

        d.addCallback(on_start, c1, cnt)
        return d

    def test_pause(self):
        def on_pause(result, c1, counter):
            self.assertEqual(c1._component_state, 'Paused')
            self.assertNotEqual(c1.counter, counter)
            self.assertFalse(c1._component_timer.running)

        def on_start(result, c1, counter):
            self.assertTrue(c1._component_timer)
            self.assertNotEqual(c1.counter, counter)
            d = component.pause(['test_pause_c1'])
            d.addCallback(on_pause, c1, counter)
            return d

        c1 = ComponentTesterUpdate('test_pause_c1')
        cnt = int(c1.counter)
        d = component.start(['test_pause_c1'])

        d.addCallback(on_start, c1, cnt)
        return d

    @defer.inlineCallbacks
    def test_component_start_error(self):
        ComponentTesterUpdate('test_pause_c1')
        yield component.start(['test_pause_c1'])
        yield component.pause(['test_pause_c1'])
        test_comp = component.get('test_pause_c1')
        try:
            result = self.failureResultOf(test_comp._component_start())
        except AttributeError:
            raise SkipTest(
                'This test requires trial failureResultOf() in Twisted version >= 13'
            )
        self.assertEqual(
            result.check(component.ComponentException), component.ComponentException
        )

    @defer.inlineCallbacks
    def test_start_paused_error(self):
        ComponentTesterUpdate('test_pause_c1')
        yield component.start(['test_pause_c1'])
        yield component.pause(['test_pause_c1'])

        # Deferreds that fail in component have to error handler which results in
        # twisted doing a log.err call which causes the test to fail.
        # Prevent failure by ignoring the exception
        self._observer._ignoreErrors(component.ComponentException)

        result = yield component.start()
        self.assertEqual(
            [(result[0][0], result[0][1].value)],
            [
                (
                    defer.FAILURE,
                    component.ComponentException(
                        'Trying to start component "%s" but it is '
                        'not in a stopped state. Current state: %s'
                        % ('test_pause_c1', 'Paused'),
                        '',
                    ),
                )
            ],
        )

    def test_shutdown(self):
        def on_shutdown(result, c1):
            self.assertTrue(c1.shutdowned)
            self.assertEqual(c1._component_state, 'Stopped')
            self.assertEqual(c1.stop_count, 1)

        def on_start(result, c1):
            d = component.shutdown()
            d.addCallback(on_shutdown, c1)
            return d

        c1 = ComponentTesterShutdown('test_shutdown_c1')
        d = component.start(['test_shutdown_c1'])
        d.addCallback(on_start, c1)
        return d
