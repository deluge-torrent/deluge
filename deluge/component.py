#
# component.py
#
# Copyright (C) 2007-2010 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#

from twisted.internet.defer import maybeDeferred, succeed, DeferredList, fail
from twisted.internet.task import LoopingCall
from deluge.log import LOG as log

class ComponentAlreadyRegistered(Exception):
    pass

class Component(object):
    """
    Component objects are singletons managed by the :class:`ComponentRegistry`.
    When a new Component object is instantiated, it will be automatically
    registered with the :class:`ComponentRegistry`.

    The ComponentRegistry has the ability to start, stop, pause and shutdown the
    components registered with it.

    **Events:**

        **start()** - This method is called when the client has connected to a
                  Deluge core.

        **stop()** - This method is called when the client has disconnected from a
                 Deluge core.

        **update()** - This method is called every 1 second by default while the
                   Componented is in a *Started* state.  The interval can be
                   specified during instantiation.  The update() timer can be
                   paused by instructing the :class:`ComponentRegistry` to pause
                   this Component.

        **shutdown()** - This method is called when the client is exiting.  If the
                     Component is in a "Started" state when this is called, a
                     call to stop() will be issued prior to shutdown().

    **States:**

        A Component can be in one of these 5 states.

        **Started** - The Component has been started by the :class:`ComponentRegistry`
                    and will have it's update timer started.

        **Starting** - The Component has had it's start method called, but it hasn't
                    fully started yet.

        **Stopped** - The Component has either been stopped or has yet to be started.

        **Stopping** - The Component has had it's stop method called, but it hasn't
                    fully stopped yet.

        **Paused** - The Component has had it's update timer stopped, but will
                    still be considered in a Started state.

    """
    def __init__(self, name, interval=1, depend=None):
        self._component_name = name
        self._component_interval = interval
        self._component_depend = depend
        self._component_state = "Stopped"
        self._component_timer = None
        self._component_starting_deferred = None
        self._component_stopping_deferred = None
        _ComponentRegistry.register(self)

    def __del__(self):
        if _ComponentRegistry:
            _ComponentRegistry.deregister(self._component_name)

    def _component_start_timer(self):
        if hasattr(self, "update"):
            self._component_timer = LoopingCall(self.update)
            self._component_timer.start(self._component_interval)

    def _component_start(self):
        def on_start(result):
            self._component_state = "Started"
            self._component_starting_deferred = None
            self._component_start_timer()
            return True

        def on_start_fail(result):
            self._component_state = "Stopped"
            self._component_starting_deferred = None
            log.error(result)
            return result

        if self._component_state == "Stopped":
            if hasattr(self, "start"):
                self._component_state = "Starting"
                d = maybeDeferred(self.start)
                d.addCallback(on_start)
                d.addErrback(on_start_fail)
                self._component_starting_deferred = d
            else:
                d = maybeDeferred(on_start, None)
        elif self._component_state == "Starting":
            return self._component_starting_deferred
        elif self._component_state == "Started":
            d = succeed(True)
        else:
            d = fail("Cannot start a component not in a Stopped state!")

        return d

    def _component_stop(self):
        def on_stop(result):
            self._component_state = "Stopped"
            if self._component_timer and self._component_timer.running:
                self._component_timer.stop()
            return True

        def on_stop_fail(result):
            self._component_state = "Started"
            self._component_stopping_deferred = None
            log.error(result)
            return result

        if self._component_state != "Stopped" and self._component_state != "Stopping":
            if hasattr(self, "stop"):
                self._component_state = "Stopping"
                d = maybeDeferred(self.stop)
                d.addCallback(on_stop)
                d.addErrback(on_stop_fail)
                self._component_stopping_deferred = d
            else:
                d = maybeDeferred(on_stop, None)

        if self._component_state == "Stopping":
            return self._component_stopping_deferred

        return succeed(None)

    def _component_pause(self):
        def on_pause(result):
            self._component_state = "Paused"

        if self._component_state == "Started":
            if self._component_timer and self._component_timer.running:
                d = maybeDeferred(self._component_timer.stop)
                d.addCallback(on_pause)
            else:
                d = succeed(None)
        elif self._component_state == "Paused":
            d = succeed(None)
        else:
            d = fail("Cannot pause a component in a non-Started state!")

        return d

    def _component_resume(self):
        def on_resume(result):
            self._component_state = "Started"

        if self._component_state == "Paused":
            d = maybeDeferred(self._component_start_timer)
            d.addCallback(on_resume)
        else:
            d = fail("Component cannot be resumed from a non-Paused state!")

        return d

    def _component_shutdown(self):
        def on_stop(result):
            if hasattr(self, "shutdown"):
                return maybeDeferred(self.shutdown)
            return succeed(None)

        d = self._component_stop()
        d.addCallback(on_stop)
        return d

    def start(self):
        pass

    def stop(self):
        pass

    def update(self):
        pass

    def shutdown(self):
        pass

class ComponentRegistry(object):
    """
    The ComponentRegistry holds a list of currently registered
    :class:`Component` objects.  It is used to manage the Components by
    starting, stopping, pausing and shutting them down.
    """
    def __init__(self):
        self.components = {}

    def register(self, obj):
        """
        Registers a component object with the registry.  This is done
        automatically when a Component object is instantiated.

        :param obj: the Component object
        :type obj: object

        :raises ComponentAlreadyRegistered: if a component with the same name is already registered.

        """
        name = obj._component_name
        if name in self.components:
            raise ComponentAlreadyRegistered(
                "Component already registered with name %s" % name)

        self.components[obj._component_name] = obj

    def deregister(self, name):
        """
        Deregisters a component from the registry.  A stop will be
        issued to the component prior to deregistering it.

        :param name: the name of the component
        :type name: string

        """

        if name in self.components:
            log.debug("Deregistering Component: %s", name)
            d = self.stop([name])
            def on_stop(result, name):
                del self.components[name]
            return d.addCallback(on_stop, name)
        else:
            return succeed(None)

    def start(self, names=[]):
        """
        Starts Components that are currently in a Stopped state and their
        dependencies.  If *names* is specified, will only start those
        Components and their dependencies and if not it will start all
        registered components.

        :param names: a list of Components to start
        :type names: list

        :returns: a Deferred object that will fire once all Components have been sucessfully started
        :rtype: twisted.internet.defer.Deferred

        """
        # Start all the components if names is empty
        if not names:
            names = self.components.keys()
        elif isinstance(names, str):
            names = [names]

        def on_depends_started(result, name):
            return self.components[name]._component_start()

        deferreds = []

        for name in names:
            if self.components[name]._component_depend:
                # This component has depends, so we need to start them first.
                d = self.start(self.components[name]._component_depend)
                d.addCallback(on_depends_started, name)
                deferreds.append(d)
            else:
                deferreds.append(self.components[name]._component_start())

        return DeferredList(deferreds)

    def stop(self, names=[]):
        """
        Stops Components that are currently not in a Stopped state.  If
        *names* is specified, then it will only stop those Components,
        and if not it will stop all the registered Components.

        :param names: a list of Components to start
        :type names: list

        :returns: a Deferred object that will fire once all Components have been sucessfully stopped
        :rtype: twisted.internet.defer.Deferred

        """
        if not names:
            names = self.components.keys()
        elif isinstance(names, str):
            names = [names]

        deferreds = []

        for name in names:
            if name in self.components:
                deferreds.append(self.components[name]._component_stop())

        return DeferredList(deferreds)

    def pause(self, names=[]):
        """
        Pauses Components that are currently in a Started state.  If
        *names* is specified, then it will only pause those Components,
        and if not it will pause all the registered Components.

        :param names: a list of Components to pause
        :type names: list

        :returns: a Deferred object that will fire once all Components have been sucessfully paused
        :rtype: twisted.internet.defer.Deferred

        """
        if not names:
            names = self.components.keys()
        elif isinstance(names, str):
            names = [names]

        deferreds = []

        for name in names:
            if self.components[name]._component_state == "Started":
                deferreds.append(self.components[name]._component_pause())

        return DeferredList(deferreds)

    def resume(self, names=[]):
        """
        Resumes Components that are currently in a Paused state.  If
        *names* is specified, then it will only resume those Components,
        and if not it will resume all the registered Components.

        :param names: a list of Components to resume
        :type names: list

        :returns: a Deferred object that will fire once all Components have been sucessfully resumed
        :rtype: twisted.internet.defer.Deferred

        """
        if not names:
            names = self.components.keys()
        elif isinstance(names, str):
            names = [names]

        deferreds = []

        for name in names:
            if self.components[name]._component_state == "Paused":
                deferreds.append(self.components[name]._component_resume())

        return DeferredList(deferreds)

    def shutdown(self):
        """
        Shutdowns all Components regardless of state.  This will call
        :meth:`stop` on call the components prior to shutting down.  This should
        be called when the program is exiting to ensure all Components have a
        chance to properly shutdown.

        :returns: a Deferred object that will fire once all Components have been sucessfully resumed
        :rtype: twisted.internet.defer.Deferred

        """
        deferreds = []

        for component in self.components.values():
            deferreds.append(component._component_shutdown())

        return DeferredList(deferreds)

    def update(self):
        """
        Updates all Components that are in a Started state.

        """
        for component in self.components.items():
            component.update()

_ComponentRegistry = ComponentRegistry()

deregister = _ComponentRegistry.deregister
start = _ComponentRegistry.start
stop = _ComponentRegistry.stop
pause = _ComponentRegistry.pause
resume = _ComponentRegistry.resume
update = _ComponentRegistry.update
shutdown = _ComponentRegistry.shutdown

def get(name):
    """
    Return a reference to a component.

    :param name: the Component name to get
    :type name: string

    :returns: the Component object
    :rtype: object

    :raises KeyError: if the Component does not exist

    """
    return _ComponentRegistry.components[name]
