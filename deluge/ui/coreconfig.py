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
from deluge.ui.client import client
from deluge.log import LOG as log

class CoreConfig(component.Component):
    def __init__(self):
        log.debug("CoreConfig init..")
        component.Component.__init__(self, "CoreConfig")
        self.config = {}
        def on_configvaluechanged_event(key, value):
            self.config[key] = value
        client.register_event_handler("ConfigValueChangedEvent", on_configvaluechanged_event)

    def start(self):
        def on_get_config(config):
            self.config = config
            return config

        return client.core.get_config().addCallback(on_get_config)

    def stop(self):
        self.config = {}

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        client.core.set_config({key: value})

    def __getattr__(self, attr):
        # We treat this directly interacting with the dictionary
        return getattr(self.config, attr)
