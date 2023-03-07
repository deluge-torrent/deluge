#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import time
from unittest.mock import Mock

import pytest
import pytest_twisted
from twisted.internet import defer, threads

import deluge.component as component


class ComponentTester(component.Component):
    def __init__(self, name, depend=None):
        super().__init__(name, depend=depend)
        event_methods = ('start', 'update', 'pause', 'resume', 'stop', 'shutdown')
        for event_method in event_methods:
            setattr(self, event_method, Mock())


class ComponentTesterDelayStart(ComponentTester):
    def __init__(self, name, depend=None):
        super().__init__(name, depend=depend)
        self.start = Mock(side_effect=self.delay)

    @pytest_twisted.inlineCallbacks
    def delay(self):
        yield threads.deferToThread(time.sleep, 0.5)


@pytest.mark.usefixtures('component')
class TestComponent:
    async def test_start_component(self):
        c = ComponentTester('test_start')
        await component.start(['test_start'])

        assert c._component_state == 'Started'
        assert c.start.call_count == 1

    async def test_start_stop_depends(self):
        c1 = ComponentTester('test_start_depends_c1')
        c2 = ComponentTester('test_start_depends_c2', depend=['test_start_depends_c1'])

        await component.start('test_start_depends_c2')

        assert c1._component_state == 'Started'
        assert c2._component_state == 'Started'
        assert c1.start.call_count == 1
        assert c2.start.call_count == 1

        await component.stop(['test_start_depends_c1'])

        assert c1._component_state == 'Stopped'
        assert c2._component_state == 'Stopped'
        assert c1.stop.call_count == 1
        assert c2.stop.call_count == 1

    async def start_with_depends(self):
        c1 = ComponentTesterDelayStart('test_start_all_c1')
        c2 = ComponentTester('test_start_all_c2', depend=['test_start_all_c4'])
        c3 = ComponentTesterDelayStart(
            'test_start_all_c3', depend=['test_start_all_c5', 'test_start_all_c1']
        )
        c4 = ComponentTester('test_start_all_c4', depend=['test_start_all_c3'])
        c5 = ComponentTester('test_start_all_c5')

        await component.start()
        return c1, c2, c3, c4, c5

    def finish_start_with_depends(self, *args):
        for c in args[1:]:
            component.deregister(c)

    async def test_start_all(self):
        components = await self.start_with_depends()
        for c in components:
            assert c._component_state == 'Started'
            assert c.start.call_count == 1

        self.finish_start_with_depends(components)

    def test_register_exception(self):
        ComponentTester('test_register_exception')
        with pytest.raises(component.ComponentAlreadyRegistered):
            ComponentTester(
                'test_register_exception',
            )

    async def test_stop(self):
        c = ComponentTester('test_stop')

        await component.start(['test_stop'])

        assert c._component_state == 'Started'

        await component.stop(['test_stop'])

        assert c._component_state == 'Stopped'
        assert not c._component_timer.running
        assert c.stop.call_count == 1

    async def test_stop_all(self):
        components = await self.start_with_depends()
        assert all(c._component_state == 'Started' for c in components)

        component.stop()
        for c in components:
            assert c._component_state == 'Stopped'
            assert c.stop.call_count == 1

        self.finish_start_with_depends(components)

    async def test_update(self):
        c = ComponentTester('test_update')
        init_update_count = int(c.update.call_count)
        await component.start(['test_update'])

        assert c._component_timer
        assert c._component_timer.running
        assert c.update.call_count != init_update_count
        await component.stop()

    async def test_pause(self):
        c = ComponentTester('test_pause')
        init_update_count = int(c.update.call_count)

        await component.start(['test_pause'])

        assert c._component_timer
        assert c.update.call_count != init_update_count

        await component.pause(['test_pause'])

        assert c._component_state == 'Paused'
        assert c.pause.call_count == 1
        assert c.update.call_count != init_update_count
        assert not c._component_timer.running

    async def test_resume(self):
        c = ComponentTester('test_resume')

        await component.start(['test_resume'])

        assert c._component_state == 'Started'

        await component.pause(['test_resume'])

        assert c._component_state == 'Paused'

        await component.resume(['test_resume'])

        assert c._component_state == 'Started'
        assert c.resume.call_count == 1
        assert c._component_timer.running

    async def test_component_start_error(self):
        ComponentTester('test_start_error')
        await component.start(['test_start_error'])
        await component.pause(['test_start_error'])
        test_comp = component.get('test_start_error')
        with pytest.raises(component.ComponentException, match='Current state: Paused'):
            await test_comp._component_start()

    async def test_start_paused_error(self):
        name = 'test_pause_error'
        ComponentTester(name)
        await component.start([name])
        await component.pause([name])

        (failure, error), *_ = await component.start()
        assert (failure, error.type, error.value.message) == (
            defer.FAILURE,
            component.ComponentException,
            (
                f'Trying to start component "{name}" but it is '
                'not in a stopped state. Current state: Paused'
            ),
        )

    async def test_shutdown(self):
        c = ComponentTester('test_shutdown')

        await component.start(['test_shutdown'])
        await component.shutdown()

        assert c.shutdown.call_count == 1
        assert c._component_state == 'Stopped'
        assert not c._component_timer.running
        assert c.stop.call_count == 1
