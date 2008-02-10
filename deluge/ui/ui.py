#
# ui.py
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

from deluge.configmanager import ConfigManager

from deluge.log import LOG as log

DEFAULT_PREFS = {
    "selected_ui": "gtk"
}

class UI:
    def __init__(self, options, args):
        log.debug("UI init..")
        config = ConfigManager("ui.conf", DEFAULT_PREFS)
        
        if options.ui != None:
            config["selected_ui"] = options.ui
        
        selected_ui = config["selected_ui"]
        config.save()
        del config
        
        if selected_ui == "gtk":
            log.info("Starting GtkUI..")
            from deluge.ui.gtkui.gtkui import GtkUI
            ui = GtkUI(args)
        elif selected_ui == "web":
            log.info("Starting WebUI..")
            from deluge.ui.webui.webui import WebUI
            ui = WebUI(args)
        elif selected_ui == "null":
            log.info("Starting NullUI..")
            from deluge.ui.null.deluge_shell import NullUI
            ui = NullUI(args)

