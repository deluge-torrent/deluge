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

from optparse import OptionParser, OptionGroup
import deluge.common
import deluge.configmanager

DEFAULT_PREFS = {
    "default_ui": "gtk"
}

class _UI(object):
    
    def __init__(self, name="gtk"):
        self.__name = name

        usage="%prog [options] [actions]", 
        
        self.__parser = OptionParser(version=deluge.common.get_version())
        
        group = OptionGroup(self.__parser, "Common Options")
        group.add_option("-c", "--config", dest="config",
            help="Set the config folder location", action="store", type="str")
        group.add_option("-l", "--logfile", dest="logfile",
            help="Output to designated logfile instead of stdout", action="store", type="str")
        group.add_option("-a", "--args", dest="args",
            help="Arguments to pass to UI, -a '--option args'", action="store", type="str")
        group.add_option("-L", "--loglevel", dest="loglevel",
            help="Set the log level: none, info, warning, error, critical, debug", action="store", type="str")
        group.add_option("-q", "--quiet", dest="quiet",
            help="Sets the log level to 'none', this is the same as `-L none`", action="store_true", default=False)
        self.__parser.add_option_group(group)
    
    @property
    def name(self):
        return self.__name
    
    @property
    def parser(self):
        return self.__parser
    
    @property
    def options(self):
        return self.__options
    
    @property
    def args(self):
        return self.__args
    
    def start(self):
        (self.__options, self.__args) = self.__parser.parse_args()
        if self.options.quiet:
            self.options.loglevel = "none"
        
        # Setup the logger
        import deluge.log
        deluge.log.setupLogger(
            level=self.options.loglevel,
            filename=self.options.logfile
        )
        
        import deluge.common
        log = deluge.log.LOG
        log.info('Deluge %s ui %s', self.name, deluge.common.get_version())
        log.debug('options: %s', self.options)
        log.debug('args: %s', self.args)
        log.info('Starting ui...')

class UI:
    def __init__(self, options, args, ui_args):
        from deluge.log import LOG as log
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
                from deluge.ui.web.web import WebUI
                ui = WebUI(args)
            elif selected_ui == "console":
                log.info("Starting ConsoleUI..")
                from deluge.ui.console.main import ConsoleUI
                ui = ConsoleUI(ui_args)
        except ImportError, e:
            import sys
            import traceback
            error_type, error_value, tb = sys.exc_info()
            stack = traceback.extract_tb(tb)
            last_frame = stack[-1]
            if last_frame[0] == __file__:
                log.error("Unable to find the requested UI: %s.  Please select a different UI with the '-u' option or alternatively use the '-s' option to select a different default UI.", selected_ui)
            else:
                log.exception(e)
                log.error("There was an error whilst launching the request UI: %s", selected_ui)
                log.error("Look at the traceback above for more information.")
            sys.exit(1)
