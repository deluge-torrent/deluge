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


from deluge.log import LOG as log

class CorePluginBase:
    def __init__(self, plugin_api, plugin_name):
        self.plugin = plugin_api
        # Register all export_* functions
        for func in dir(self):
            if func.startswith("export_"):
                log.debug("Registering export function %s as %s", func,
                    plugin_name.lower() + "_" + func[7:])
                self.plugin.get_core().register_function(
                    getattr(self, "%s" % func), plugin_name.lower()\
                         + "_" + func[7:])
        log.debug("CorePlugin initialized..")

