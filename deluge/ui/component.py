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
    def __init__(self, name):
        # Register with the ComponentRegistry
        register(name, self)
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
        
    def update(self):
        pass
        
        
class ComponentRegistry:
    def __init__(self):
        self.components = {}
        self.update_timer = None
    
    def register(self, name, obj):
        """Registers a component"""
        log.debug("Registered %s with ComponentRegistry..", name)
        self.components[name] = obj
    
    def get(self, name):
        """Returns a reference to the component 'name'"""
        return self.components[name]
        
    def start(self, update_interval=1000):
        """Starts all components"""
        for component in self.components.keys():
            self.components[component].start()
            self.components[component]._start()

        # Start the update timer
        self.update_timer = gobject.timeout_add(update_interval, self.update)
        # Do an update right away
        self.update()
        
    def stop(self):
        """Stops all components"""
        for component in self.components.keys():
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
    
_ComponentRegistry = ComponentRegistry()

def register(name, obj):
    """Registers a UI component with the registry"""
    _ComponentRegistry.register(name, obj)

def start():
    """Starts all components"""
    _ComponentRegistry.start()

def stop():
    """Stops all components"""
    _ComponentRegistry.stop()

def update():
    """Updates all components"""
    _ComponentRegistry.update()

def get(component):
    """Return a reference to the component"""
    return _ComponentRegistry.get(component)
