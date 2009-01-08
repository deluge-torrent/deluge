#
# ui.py
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

import sys
import deluge.configmanager

from deluge.log import LOG as log

DEFAULT_PREFS = {
    "default_ui": "gtk"
}

class UI:
    def __init__(self, options, args, ui_args):
        log.debug("UI init..")

        # Set the config directory
        deluge.configmanager.set_config_dir(options.config)

        config = deluge.configmanager.ConfigManager("ui.conf", DEFAULT_PREFS)

        if not options.ui:
            selected_ui = config["default_ui"]
        else:
            selected_ui = options.ui

        config.save()
        del config

        try:
            if selected_ui == "gtk":
                log.info("Starting GtkUI..")
                from deluge.ui.gtkui.gtkui import GtkUI
                ui = GtkUI(args)
            elif selected_ui == "web":
                log.info("Starting WebUI..")
                from deluge.ui.webui.webui import WebUI
                ui = WebUI(args)
            elif selected_ui == "console":
                log.info("Starting ConsoleUI..")
                from deluge.ui.console.main import ConsoleUI
                ui = ConsoleUI(ui_args).run()
        except ImportError:
            log.error("Unable to find the requested UI.  Please select a different UI with the '-u' option or alternatively use the '-s' option to select a different default UI.")
            sys.exit(0)
