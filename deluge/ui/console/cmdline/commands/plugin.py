# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import deluge.component as component
import deluge.configmanager
from deluge.ui.client import client

from . import BaseCommand


class Command(BaseCommand):
    """Manage plugins"""

    def add_arguments(self, parser):
        parser.add_argument(
            '-l',
            '--list',
            action='store_true',
            default=False,
            dest='list',
            help=_('Lists available plugins'),
        )
        parser.add_argument(
            '-s',
            '--show',
            action='store_true',
            default=False,
            dest='show',
            help=_('Shows enabled plugins'),
        )
        parser.add_argument(
            '-e', '--enable', dest='enable', nargs='+', help=_('Enables a plugin')
        )
        parser.add_argument(
            '-d', '--disable', dest='disable', nargs='+', help=_('Disables a plugin')
        )
        parser.add_argument(
            '-r',
            '--reload',
            action='store_true',
            default=False,
            dest='reload',
            help=_('Reload list of available plugins'),
        )
        parser.add_argument(
            '-i', '--install', help=_('Install a plugin from an .egg file')
        )

    def handle(self, options):
        self.console = component.get('ConsoleUI')

        if options.reload:
            client.core.pluginmanager.rescan_plugins()
            self.console.write('{!green!}Plugin list successfully reloaded')
            return

        elif options.list:

            def on_available_plugins(result):
                self.console.write('{!info!}Available Plugins:')
                for p in result:
                    self.console.write('{!input!}  ' + p)

            return client.core.get_available_plugins().addCallback(on_available_plugins)

        elif options.show:

            def on_enabled_plugins(result):
                self.console.write('{!info!}Enabled Plugins:')
                for p in result:
                    self.console.write('{!input!}  ' + p)

            return client.core.get_enabled_plugins().addCallback(on_enabled_plugins)

        elif options.enable:

            def on_available_plugins(result):
                plugins = {}
                for p in result:
                    plugins[p.lower()] = p
                for arg in options.enable:
                    if arg.lower() in plugins:
                        client.core.enable_plugin(plugins[arg.lower()])

            return client.core.get_available_plugins().addCallback(on_available_plugins)

        elif options.disable:

            def on_enabled_plugins(result):
                plugins = {}
                for p in result:
                    plugins[p.lower()] = p
                for arg in options.disable:
                    if arg.lower() in plugins:
                        client.core.disable_plugin(plugins[arg.lower()])

            return client.core.get_enabled_plugins().addCallback(on_enabled_plugins)

        elif options.install:
            import os.path
            import shutil
            from base64 import b64encode

            filepath = options.install

            if not os.path.exists(filepath):
                self.console.write('{!error!}Invalid path: %s' % filepath)
                return

            config_dir = deluge.configmanager.get_config_dir()
            filename = os.path.split(filepath)[1]
            shutil.copyfile(filepath, os.path.join(config_dir, 'plugins', filename))

            client.core.rescan_plugins()

            if not client.is_localhost():
                # We need to send this plugin to the daemon
                with open(filepath, 'rb') as _file:
                    filedump = b64encode(_file.read())
                try:
                    client.core.upload_plugin(filename, filedump)
                    client.core.rescan_plugins()
                except Exception:
                    self.console.write(
                        '{!error!}An error occurred, plugin was not installed'
                    )

            self.console.write(
                '{!green!}Plugin was successfully installed: %s' % filename
            )

    def complete(self, line):
        return component.get('ConsoleUI').tab_complete_path(
            line, ext='.egg', sort='name', dirs_first=-1
        )
