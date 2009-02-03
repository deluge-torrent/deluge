#
# coreconfig.py
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
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
from deluge.ui.client import client
from deluge.log import LOG as log

class CoreConfig(component.Component):
    def __init__(self):
        log.debug("CoreConfig init..")
        component.Component.__init__(self, "CoreConfig", ["Signals"])
        self.config = {}
        client.register_event_handler("ConfigValueChangedEvent", self.on_configvaluechanged_event)

    def start(self):
        client.core.get_config().addCallback(self._on_get_config)

    def stop(self):
        self.config = {}

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        client.core.set_config({key: value})

    def _on_get_config(self, config):
        self.config = config

    def on_configvaluechanged_event(self, key, value):
        self.config[key] = value
