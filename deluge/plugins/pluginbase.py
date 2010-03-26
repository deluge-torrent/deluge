#
# pluginbase.py
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

import deluge.component as component
from deluge.log import LOG as log

class PluginBase(component.Component):

    update_interval = 1

    def __init__(self, name):
        super(PluginBase, self).__init__(name, self.update_interval)
                    
    def enable(self):
        raise NotImplementedError("Need to define an enable method!")

    def disable(self):
        raise NotImplementedError("Need to define a disable method!")

class CorePluginBase(PluginBase):
    def __init__(self, plugin_name):
        super(CorePluginBase, self).__init__("CorePlugin." + plugin_name)
        # Register RPC methods
        component.get("RPCServer").register_object(self, plugin_name.lower())
        log.debug("CorePlugin initialized..")

class GtkPluginBase(PluginBase):
    def __init__(self, plugin_name):
        super(GtkPluginBase, self).__init__("GtkPlugin." + plugin_name)
        log.debug("GtkPlugin initialized..")

class WebPluginBase(PluginBase):
    
    scripts = []
    debug_scripts = []
    
    stylesheets = []
    debug_stylesheets = []
    
    def __init__(self, plugin_name):
        super(WebPluginBase, self).__init__("WebPlugin." + plugin_name)
        
        # Register JSON rpc methods
        component.get("JSON").register_object(self, plugin_name.lower())
        log.debug("WebPlugin initialized..")
    
    def enable(self):
        pass

    def disable(self):
        pass
