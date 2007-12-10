#
# component.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
# 	Boston, MA    02110-1301, USA.
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

import gobject
from deluge.log import LOG as log

COMPONENT_STATE = [
    "Stopped",
    "Started"
]

class Component:
    def __init__(self, name, depend=None):
        # Register with the ComponentRegistry
        register(name, self, depend)
        self._state = COMPONENT_STATE.index("Stopped")
    
    def get_state(self):
        return self._state
        
    def start(self):
        pass
    
    def _start(self):
        self._state = COMPONENT_STATE.index("Started")
        
    def stop(self):
        pass

    def _stop(self):
        self._state = COMPONENT_STATE.index("Stopped")
        
    def shutdown(self):
        pass
        
    def update(self):
        pass
        
        
class ComponentRegistry:
    def __init__(self):
        self.components = {}
        self.depend = {}
        self.update_timer = None
    
    def register(self, name, obj, depend):
        """Registers a component.. depend must be list or None"""
        log.debug("Registered %s with ComponentRegistry..", name)
        self.components[name] = obj
        if depend != None:
            self.depend[name] = depend
    
    def get(self, name):
        """Returns a reference to the component 'name'"""
        return self.components[name]
        
    def start(self, update_interval=1000):
        """Starts all components"""
        for component in self.components.keys():
            self.start_component(component)

        # Start the update timer
        self.update_timer = gobject.timeout_add(update_interval, self.update)
        # Do an update right away
        self.update()
    
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
            log.debug("Stopping component %s..", component)
            self.components[component].stop()
            self.components[component]._stop()
        # Stop the update timer
        gobject.source_remove(self.update_timer)

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

def start():
    """Starts all components"""
    _ComponentRegistry.start()

def stop():
    """Stops all components"""
    _ComponentRegistry.stop()

def update():
    """Updates all components"""
    _ComponentRegistry.update()

def shutdown():
    """Shutdowns all components"""
    _ComponentRegistry.shutdown()
    
def get(component):
    """Return a reference to the component"""
    return _ComponentRegistry.get(component)
