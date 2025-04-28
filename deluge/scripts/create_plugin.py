"""
Creates an empty plugin and links it from ~/.config/deluge/plugins
This plugin includes the framework for using the preferences dialog

example:
python create_plugin.py --name MyPlugin2 --basepath . --author-name "Your Name" --author-email "yourname@example.com"

"""

import os
import sys
from argparse import ArgumentParser
from datetime import datetime

import deluge.common

parser = ArgumentParser()
parser.add_argument(
    '-n', '--name', metavar='<plugin name>', required=True, help='Plugin name'
)
parser.add_argument('-m', '--module-name', metavar='<module name>', help='Module name')
parser.add_argument(
    '-p', '--basepath', metavar='<path>', required=True, help='Base path'
)
parser.add_argument(
    '-a',
    '--author-name',
    metavar='<author name>',
    required=True,
    help='Author name,for the GPL header',
)
parser.add_argument(
    '-e',
    '--author-email',
    metavar='<author email>',
    required=True,
    help='Author email,for the GPL header',
)
parser.add_argument('-u', '--url', metavar='<URL>', help='Homepage URL')
parser.add_argument(
    '-c',
    '--config',
    metavar='<Config dir>',
    dest='configdir',
    help='Location of deluge configuration',
)

options = parser.parse_args()


def create_plugin():
    if not options.url:
        options.url = ''

    if not os.path.exists(options.basepath):
        print('basepath does not exist')
        return

    if not options.configdir:
        options.configdir = deluge.common.get_default_config_dir()

    options.configdir = os.path.realpath(options.configdir)

    real_name = options.name
    name = real_name.replace(' ', '_')
    safe_name = name.lower()
    if options.module_name:
        safe_name = options.module_name.lower()
    plugin_base = os.path.realpath(os.path.join(options.basepath, name))
    src = os.path.join(plugin_base, 'deluge_' + safe_name)
    data_dir = os.path.join(src, 'data')
    python_path = sys.executable

    if os.path.exists(plugin_base):
        print('the directory %s already exists, delete it first' % plugin_base)
        return

    def write_file(path, filename, template, include_gpl=True):
        plugin_args = {
            'author_name': options.author_name,
            'author_email': options.author_email,
            'name': name,
            'safe_name': safe_name,
            'filename': filename,
            'plugin_base': plugin_base,
            'python_path': python_path,
            'url': options.url,
            'configdir': options.configdir,
            'current_year': datetime.utcnow().year,
        }

        filename = os.path.join(path, filename)
        with open(filename, 'w') as _file:
            if filename.endswith('.py') and include_gpl:
                _file.write(GPL % plugin_args)
            _file.write(template % plugin_args)

    print('creating folders..')
    os.mkdir(plugin_base)
    os.mkdir(src)
    os.mkdir(data_dir)

    print('creating files..')
    write_file(plugin_base, 'setup.py', SETUP)
    write_file(src, '__init__.py', INIT)
    write_file(src, 'gtk3ui.py', GTK3UI)
    write_file(src, 'webui.py', WEBUI)
    write_file(src, 'core.py', CORE)
    write_file(src, 'common.py', COMMON)
    write_file(data_dir, 'config.ui', GLADE)
    write_file(data_dir, '%s.js' % safe_name, DEFAULT_JS)

    # add an input parameter for this?
    print('building dev-link..')
    if deluge.common.windows_check():
        write_file(plugin_base, 'create_dev_link.bat', CREATE_DEV_LINK_WIN)
        dev_link_path = os.path.join(plugin_base, 'create_dev_link.bat')
    else:
        write_file(plugin_base, 'create_dev_link.sh', CREATE_DEV_LINK_NIX)
        dev_link_path = os.path.join(plugin_base, 'create_dev_link.sh')
        os.system('chmod +x %s' % dev_link_path)  # lazy..
    os.system(dev_link_path)


CORE = """from __future__ import unicode_literals

import logging

import deluge.configmanager
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase

log = logging.getLogger(__name__)

DEFAULT_PREFS = {
    'test': 'NiNiNi'
}


class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager(
            '%(safe_name)s.conf', DEFAULT_PREFS)

    def disable(self):
        pass

    def update(self):
        pass

    @export
    def set_config(self, config):
        \"\"\"Sets the config dictionary\"\"\"
        for key in config:
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        \"\"\"Returns the config dictionary\"\"\"
        return self.config.config
"""

INIT = """from deluge.plugins.init import PluginInitBase


class CorePlugin(PluginInitBase):
    def __init__(self, plugin_name):
        from .core import Core as PluginClass
        self._plugin_cls = PluginClass
        super(CorePlugin, self).__init__(plugin_name)


class Gtk3UIPlugin(PluginInitBase):
    def __init__(self, plugin_name):
        from .gtk3ui import Gtk3UI as PluginClass
        self._plugin_cls = PluginClass
        super(Gtk3UIPlugin, self).__init__(plugin_name)


class WebUIPlugin(PluginInitBase):
    def __init__(self, plugin_name):
        from .webui import WebUI as PluginClass
        self._plugin_cls = PluginClass
        super(WebUIPlugin, self).__init__(plugin_name)
"""


SETUP = """from setuptools import find_packages, setup

__plugin_name__ = '%(name)s'
__author__ = '%(author_name)s'
__author_email__ = '%(author_email)s'
__version__ = '0.1'
__url__ = '%(url)s'
__license__ = 'GPLv3'
__description__ = ''
__long_description__ = \"\"\"\"\"\"
__pkg_data__ = {'deluge_'+__plugin_name__.lower(): ['data/*']}

setup(
    name=__plugin_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    long_description=__long_description__,

    packages=find_packages(),
    package_data=__pkg_data__,

    entry_points=\"\"\"
    [deluge.plugin.core]
    %%s = deluge_%%s:CorePlugin
    [deluge.plugin.gtk3ui]
    %%s = deluge_%%s:Gtk3UIPlugin
    [deluge.plugin.web]
    %%s = deluge_%%s:WebUIPlugin
    \"\"\" %% ((__plugin_name__, __plugin_name__.lower()) * 3)
)
"""

COMMON = """from __future__ import unicode_literals

import os.path

from pkg_resources import resource_filename


def get_resource(filename):
    return resource_filename(__package__, os.path.join('data', filename))
"""

GTK3UI = """from __future__ import unicode_literals

import logging

from gi.repository import Gtk

import deluge.component as component
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client

from .common import get_resource

log = logging.getLogger(__name__)


class Gtk3UI(Gtk3PluginBase):
    def enable(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('config.ui'))

        component.get('Preferences').add_page(
            '%(name)s', self.builder.get_object('prefs_box'))
        component.get('PluginManager').register_hook(
            'on_apply_prefs', self.on_apply_prefs)
        component.get('PluginManager').register_hook(
            'on_show_prefs', self.on_show_prefs)

    def disable(self):
        component.get('Preferences').remove_page('%(name)s')
        component.get('PluginManager').deregister_hook(
            'on_apply_prefs', self.on_apply_prefs)
        component.get('PluginManager').deregister_hook(
            'on_show_prefs', self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug('applying prefs for %(name)s')
        config = {
            'test': self.builder.get_object('txt_test').get_text()
        }
        client.%(safe_name)s.set_config(config)

    def on_show_prefs(self):
        client.%(safe_name)s.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        \"\"\"callback for on show_prefs\"\"\"
        self.builder.get_object('txt_test').set_text(config['test'])
"""

GLADE = """<?xml version="1.0" encoding="UTF-8"?>
<!-- Generated with glade 3.18.3 -->
<interface>
  <requires lib="gtk+" version="3.0"/>
  <object class="GtkWindow" id="window1">
    <child>
      <object class="GtkBox" id="prefs_box">
        <property name="visible">True</property>
        <child>
          <object class="GtkLabel" id="label1">
            <property name="visible">True</property>
            <property name="label" translatable="yes">Test config value:</property>
          </object>
        </child>
        <child>
          <object class="GtkEntry" id="txt_test">
            <property name="visible">True</property>
            <property name="can_focus">True</property>
          </object>
          <packing>
            <property name="position">1</property>
          </packing>
        </child>
      </object>
    </child>
  </object>
</interface>
"""

WEBUI = """from __future__ import unicode_literals

import logging

from deluge.plugins.pluginbase import WebPluginBase

from .common import get_resource

log = logging.getLogger(__name__)


class WebUI(WebPluginBase):

    scripts = [get_resource('%(safe_name)s.js')]

    def enable(self):
        pass

    def disable(self):
        pass
"""

DEFAULT_JS = """/**
 * Script: %(filename)s
 *     The client-side javascript code for the %(name)s plugin.
 *
 * Copyright:
 *     (C) %(author_name)s %(current_year)s <%(author_email)s>
 *
 *     This file is part of %(name)s and is licensed under GNU GPL 3.0, or
 *     later, with the additional special exception to link portions of this
 *     program with the OpenSSL library. See LICENSE for more details.
 */

%(name)sPlugin = Ext.extend(Deluge.Plugin, {
    constructor: function(config) {
        config = Ext.apply({
            name: '%(name)s'
        }, config);
        %(name)sPlugin.superclass.constructor.call(this, config);
    },

    onDisable: function() {
        deluge.preferences.removePage(this.prefsPage);
    },

    onEnable: function() {
        this.prefsPage = deluge.preferences.addPage(
            new Deluge.ux.preferences.%(name)sPage());
    }
});
new %(name)sPlugin();
"""

GPL = """# -*- coding: utf-8 -*-
# Copyright (C) %(current_year)d %(author_name)s <%(author_email)s>
#
# Basic plugin template created by the Deluge Team.
#
# This file is part of %(name)s and is licensed under GNU GPL 3.0, or later,
# with the additional special exception to link portions of this program with
# the OpenSSL library. See LICENSE for more details.
"""

CREATE_DEV_LINK_NIX = """#!/bin/bash
BASEDIR=$(cd `dirname $0` && pwd)
CONFIG_DIR=$( test -z $1 && echo "%(configdir)s" || echo "$1")
[ -d "$CONFIG_DIR/plugins" ] || echo "Config dir \"$CONFIG_DIR\" is either not a directory \
or is not a proper deluge config directory. Exiting"
[ -d "$CONFIG_DIR/plugins" ] || exit 1
cd $BASEDIR
test -d $BASEDIR/temp || mkdir $BASEDIR/temp
export PYTHONPATH=$BASEDIR/temp
%(python_path)s setup.py build develop --install-dir $BASEDIR/temp
cp $BASEDIR/temp/*.egg-link $CONFIG_DIR/plugins
rm -fr $BASEDIR/temp
"""

CREATE_DEV_LINK_WIN = """@echo off
set BASEDIR=%%~dp0
set BASEDIR=%%BASEDIR:~0,-1%%
if [%%1]==[] (
    set CONFIG_DIR=%(configdir)s
) else (
    set CONFIG_DIR=%%1
)
if not exist %%CONFIG_DIR%%\\plugins (
    echo Config dir %%CONFIG_DIR%% is either not a directory \
or is not a proper deluge config directory. Exiting
    exit /b 1
)
cd %%BASEDIR%%
if not exist %%BASEDIR%%\\temp (
    md %%BASEDIR%%\\temp
)
set PYTHONPATH=%%BASEDIR%%/temp
%(python_path)s setup.py build develop --install-dir %%BASEDIR%%\\temp
copy "%%BASEDIR%%\\temp\\*.egg-link" "%%CONFIG_DIR%%\\plugins"
rd /s /q %%BASEDIR%%\\temp
"""

create_plugin()
