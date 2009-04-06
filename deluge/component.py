#
# component.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
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


import gobject
from deluge.log import LOG as log

COMPONENT_STATE = [
    "Stopped",
    "Started",
    "Paused"
]

class Component:
    def __init__(self, name, interval=1000, depend=None):
        # Register with the ComponentRegistry
        register(name, self, depend)
        self._interval = interval
        self._timer = None
        self._state = COMPONENT_STATE.index("Stopped")

    def get_state(self):
        return self._state

    def start(self):
        pass

    def _start(self):
        self._state = COMPONENT_STATE.index("Started")
        if self._update():
            self._timer = gobject.timeout_add(self._interval, self._update)

    def stop(self):
        pass

    def _stop(self):
        self._state = COMPONENT_STATE.index("Stopped")
        try:
            gobject.source_remove(self._timer)
        except:
            pass

    def _pause(self):
        self._state = COMPONENT_STATE.index("Paused")
        try:
            gobject.source_remove(self._timer)
        except:
            pass

    def _resume(self):
        self._start()

    def shutdown(self):
        pass

    def _update(self):
        try:
            self.update()
        except AttributeError:
            # This will stop the timer since the component doesn't have an
            # update method.
            return False
        return True


class ComponentRegistry:
    def __init__(self):
        self.components = {}
        self.depend = {}

    def register(self, name, obj, depend):
        """Registers a component.. depend must be list or None"""
        log.debug("Registered %s with ComponentRegistry..", name)
        self.components[name] = obj
        if depend != None:
            self.depend[name] = depend

    def get(self, name):
        """Returns a reference to the component 'name'"""
        return self.components[name]

    def start(self):
        """Starts all components"""
        for component in self.components.keys():
            self.start_component(component)

    def start_component(self, name):
        """Starts a component"""
        # Check to see if this component has any dependencies
        if self.depend.has_key(name):
            for depend in self.depend[name]:
                self.start_component(depend)
        # Only start if the component is stopped.
        if self.components[name].get_state() == \
            COMPONENT_STATE.index("Stopped"):
            log.debug("Starting component %s..", name)
            self.components[name].start()
            self.components[name]._start()

    def stop(self):
        """Stops all components"""
        for component in self.components.keys():
            self.stop_component(component)

    def stop_component(self, component):
        if self.components[component].get_state() != \
                COMPONENT_STATE.index("Stopped"):
            log.debug("Stopping component %s..", component)
            self.components[component].stop()
            self.components[component]._stop()

    def pause(self):
        """Pauses all components.  Stops calling update()"""
        for component in self.components.keys():
            self.pause_component(component)

    def pause_component(self, component):
        if self.components[component].get_state() not in \
            [COMPONENT_STATE.index("Paused"), COMPONENT_STATE.index("Stopped")]:
            log.debug("Pausing component %s..", component)
            self.components[component]._pause()

    def resume(self):
        """Resumes all components.  Starts calling update()"""
        for component in self.components.keys():
            self.resume_component(component)

    def resume_component(self, component):
        if self.components[component].get_state() == COMPONENT_STATE.index("Paused"):
            log.debug("Resuming component %s..", component)
            self.components[component]._resume()

    def update(self):
        """Updates all components"""
        for component in self.components.keys():
            # Only update the component if it's started
            if self.components[component].get_state() == \
                COMPONENT_STATE.index("Started"):
                self.components[component].update()

        return True

    def shutdown(self):
        """Shuts down all components.  This should be called when the program
        exits so that components can do any necessary clean-up."""
        # Stop all components first
        self.stop()
        for component in self.components.keys():
            log.debug("Shutting down component %s..", component)
            try:
                self.components[component].shutdown()
            except Exception, e:
                log.debug("Unable to call shutdown(): %s", e)


_ComponentRegistry = ComponentRegistry()

def register(name, obj, depend=None):
    """Registers a component with the registry"""
    _ComponentRegistry.register(name, obj, depend)

def start(component=None):
    """Starts all components"""
    if component == None:
        _ComponentRegistry.start()
    else:
        _ComponentRegistry.start_component(component)

def stop(component=None):
    """Stops all or specified components"""
    if component == None:
        _ComponentRegistry.stop()
    else:
        _ComponentRegistry.stop_component(component)

def pause(component=None):
    """Pauses all or specificed components"""
    if component == None:
        _ComponentRegistry.pause()
    else:
        _ComponentRegistry.pause_component(component)

def resume(component=None):
    """Resumes all or specificed components"""
    if component == None:
        _ComponentRegistry.resume()
    else:
        _ComponentRegistry.resume_component(component)

def update():
    """Updates all components"""
    _ComponentRegistry.update()

def shutdown():
    """Shutdowns all components"""
    _ComponentRegistry.shutdown()

def get(component):
    """Return a reference to the component"""
    return _ComponentRegistry.get(component)
