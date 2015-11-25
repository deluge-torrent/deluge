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

import os
import sys
from optparse import OptionParser, OptionGroup

import deluge.common
import deluge.configmanager
import deluge.log

try:
    from setproctitle import setproctitle
except ImportError:
    setproctitle = lambda t: None

def version_callback(option, opt_str, value, parser):
    print os.path.basename(sys.argv[0]) + ": " + deluge.common.get_version()
    try:
        from deluge._libtorrent import lt
        print "libtorrent: %s" % lt.version
    except ImportError:
        pass
    raise SystemExit

DEFAULT_PREFS = {
    "default_ui": "gtk"
}

if 'dev' not in deluge.common.get_version():
    import warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='twisted')

class _UI(object):

    def __init__(self, name="gtk"):
        self.__name = name

        self.__parser = OptionParser(usage="%prog [options] [actions]")
        self.__parser.add_option("-v", "--version", action="callback", callback=version_callback,
            help="Show program's version number and exit")
        group = OptionGroup(self.__parser, "Common Options")
        group.add_option("-c", "--config", dest="config",
            help="Set the config folder location", action="store", type="str")
        group.add_option("-l", "--logfile", dest="logfile",
            help="Output to designated logfile instead of stdout", action="store", type="str")
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
        if deluge.common.windows_check():
            (self.__options, self.__args) = self.__parser.parse_args(deluge.common.win32_unicode_argv()[1:])
        else:
            (self.__options, self.__args) = self.__parser.parse_args()

        if self.__options.quiet:
            self.__options.loglevel = "none"

        if self.__options.loglevel:
            self.__options.loglevel = self.__options.loglevel.lower()

        # Setup the logger
        deluge.log.setupLogger(level=self.__options.loglevel, filename=self.__options.logfile)
        log = deluge.log.LOG

        if self.__options.config:
            if not deluge.configmanager.set_config_dir(self.__options.config):
                log.error("There was an error setting the config dir! Exiting..")
                sys.exit(1)

        setproctitle("deluge-%s" % self.__name)

        log.info("Deluge ui %s", deluge.common.get_version())
        log.debug("options: %s", self.__options)
        log.debug("args: %s", self.__args)
        log.info("Starting %s ui..", self.__name)

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

        setproctitle("deluge")

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
