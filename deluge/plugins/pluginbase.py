#
# core.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
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
# 	Boston, MA    02110-1301, USA.
#

import deluge.component as component
from deluge.log import LOG as log

class PluginBase(component.Component):
    def enable(self):
        raise NotImplementedError("Need to define an enable method!")

    def disable(self):
        raise NotImplementedError("Need to define a disable method!")

class CorePluginBase(PluginBase):
    def __init__(self, plugin_name):
        component.Component.__init__(self, "CorePlugin." + plugin_name)
        # Register RPC methods
        component.get("RPCServer").register_object(self, plugin_name.lower())
        log.debug("CorePlugin initialized..")
        component.start("CorePlugin." + plugin_name)

class GtkPluginBase(PluginBase):
    def __init__(self, plugin_name):
        component.Component.__init__(self, "GtkPlugin." + plugin_name)
        log.debug("GtkPlugin initialized..")
        component.start("GtkPlugin." + plugin_name)

class WebPluginBase(PluginBase):
    def __init__(self, plugin_name):
        component.Component.__init__(self, "WebPlugin." + plugin_name)
        log.debug("WebPlugin initialized..")
        component.start("WebPlugin." + plugin_name)
