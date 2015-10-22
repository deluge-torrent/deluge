# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from optparse import make_option

import deluge.component as component
import deluge.configmanager
from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand


class Command(BaseCommand):
    """Manage plugins with this command"""
    option_list = BaseCommand.option_list + (
        make_option("-l", "--list", action="store_true", default=False, dest="list",
                    help="Lists available plugins"),
        make_option("-s", "--show", action="store_true", default=False, dest="show",
                    help="Shows enabled plugins"),
        make_option("-e", "--enable", dest="enable",
                    help="Enables a plugin"),
        make_option("-d", "--disable", dest="disable",
                    help="Disables a plugin"),
        make_option("-r", "--reload", action="store_true", default=False, dest="reload",
                    help="Reload list of available plugins"),
        make_option("-i", "--install", dest="plugin_file",
                    help="Install a plugin from an .egg file"),
    )
    usage = """Usage: plugin [ -l | --list ]
       plugin [ -s | --show ]
       plugin [ -e | --enable ] <plugin-name>
       plugin [ -d | --disable ] <plugin-name>
       plugin [ -i | --install ] <plugin-file>
       plugin [ -r | --reload]"""

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")

        if len(args) == 0 and not any(options.values()):
            self.console.write(self.usage)
            return

        if options["reload"]:
            client.core.pluginmanager.rescan_plugins()
            self.console.write("{!green!}Plugin list successfully reloaded")
            return

        elif options["list"]:
            def on_available_plugins(result):
                self.console.write("{!info!}Available Plugins:")
                for p in result:
                    self.console.write("{!input!}  " + p)

            return client.core.get_available_plugins().addCallback(on_available_plugins)

        elif options["show"]:
            def on_enabled_plugins(result):
                self.console.write("{!info!}Enabled Plugins:")
                for p in result:
                    self.console.write("{!input!}  " + p)

            return client.core.get_enabled_plugins().addCallback(on_enabled_plugins)

        elif options["enable"]:
            def on_available_plugins(result):
                plugins = {}
                for p in result:
                    plugins[p.lower()] = p
                p_args = [options["enable"]] + list(args)

                for arg in p_args:
                    if arg.lower() in plugins:
                        client.core.enable_plugin(plugins[arg.lower()])

            return client.core.get_available_plugins().addCallback(on_available_plugins)

        elif options["disable"]:
            def on_enabled_plugins(result):
                plugins = {}
                for p in result:
                    plugins[p.lower()] = p
                p_args = [options["disable"]] + list(args)

                for arg in p_args:
                    if arg.lower() in plugins:
                        client.core.disable_plugin(plugins[arg.lower()])

            return client.core.get_enabled_plugins().addCallback(on_enabled_plugins)

        elif options["plugin_file"]:

            filepath = options["plugin_file"]

            import os.path
            import base64
            import shutil

            if not os.path.exists(filepath):
                self.console.write("{!error!}Invalid path: %s" % filepath)
                return

            config_dir = deluge.configmanager.get_config_dir()
            filename = os.path.split(filepath)[1]

            shutil.copyfile(
                filepath,
                os.path.join(config_dir, "plugins", filename))

            client.core.rescan_plugins()

            if not client.is_localhost():
                # We need to send this plugin to the daemon
                filedump = base64.encodestring(open(filepath, "rb").read())
                try:
                    client.core.upload_plugin(filename, filedump)
                    client.core.rescan_plugins()
                except Exception:
                    self.console.write("{!error!}An error occurred, plugin was not installed")

            self.console.write("{!green!}Plugin was successfully installed: %s" % filename)

    def complete(self, line):
        return component.get("ConsoleUI").tab_complete_path(line, ext=".egg", sort="name", dirs_first=-1)
