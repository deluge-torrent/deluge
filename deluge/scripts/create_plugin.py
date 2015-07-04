"""
Creates an empty plugin and links it from ~/.config/deluge/plugins
This plugin includes the framework for using the preferences dialog

example:
python create_plugin.py --name MyPlugin2 --basepath . --author-name "Your Name" --author-email "yourname@example.com"

"""
from __future__ import print_function

import os
import sys
from datetime import datetime
from optparse import OptionParser

import deluge.common

parser = OptionParser()
parser.add_option("-n", "--name", dest="name", help="plugin name")
parser.add_option("-m", "--module-name", dest="module", help="plugin name")
parser.add_option("-p", "--basepath", dest="path", help="base path")
parser.add_option("-a", "--author-name", dest="author_name", help="author name,for the GPL header")
parser.add_option("-e", "--author-email", dest="author_email", help="author email,for the GPL header")
parser.add_option("-u", "--url", dest="url", help="Homepage URL")
parser.add_option("-c", "--config", dest="configdir", help="location of deluge configuration")


(options, args) = parser.parse_args()


def create_plugin():
    if not options.name:
        print("--name is mandatory , use -h for more info")
        return
    if not options.path:
        print("--basepath is mandatory , use -h for more info")
        return
    if not options.author_email:
        print("--author-email is mandatory , use -h for more info")
        return
    if not options.author_email:
        print("--author-name is mandatory , use -h for more info")
        return

    if not options.url:
        options.url = ""

    if not os.path.exists(options.path):
        print("basepath does not exist")
        return

    if not options.configdir:
        options.configdir = deluge.common.get_default_config_dir()

    options.configdir = os.path.realpath(options.configdir)

    real_name = options.name
    name = real_name.replace(" ", "_")
    safe_name = name.lower()
    if options.module:
        safe_name = options.module.lower()
    plugin_base = os.path.realpath(os.path.join(options.path, name))
    deluge_namespace = os.path.join(plugin_base, "deluge")
    plugins_namespace = os.path.join(deluge_namespace, "plugins")
    src = os.path.join(plugins_namespace, safe_name)
    data_dir = os.path.join(src, "data")
    python_path = sys.executable

    if os.path.exists(plugin_base):
        print("the directory %s already exists, delete it first" % plugin_base)
        return

    def write_file(path, filename, template, include_gpl=True):
        args = {
            "author_name": options.author_name,
            "author_email": options.author_email,
            "name": name,
            "safe_name": safe_name,
            "filename": filename,
            "plugin_base": plugin_base,
            "python_path": python_path,
            "url": options.url,
            "configdir": options.configdir,
            "current_year": datetime.utcnow().year
        }

        filename = os.path.join(path, filename)
        f = open(filename, "w")
        if filename.endswith(".py") and include_gpl:
            f.write(GPL % args)
        f.write(template % args)
        f.close()

    print("creating folders..")
    os.mkdir(plugin_base)
    os.mkdir(deluge_namespace)
    os.mkdir(plugins_namespace)
    os.mkdir(src)
    os.mkdir(data_dir)

    print("creating files..")
    write_file(plugin_base, "setup.py", SETUP)
    write_file(deluge_namespace, "__init__.py", NAMESPACE_INIT, False)
    write_file(plugins_namespace, "__init__.py", NAMESPACE_INIT, False)
    write_file(src, "__init__.py", INIT)
    write_file(src, "gtkui.py", GTKUI)
    write_file(src, "webui.py", WEBUI)
    write_file(src, "core.py", CORE)
    write_file(src, "common.py", COMMON)
    write_file(data_dir, "config.glade", GLADE)
    write_file(data_dir, "%s.js" % safe_name, DEFAULT_JS)

    # add an input parameter for this?
    print("building dev-link..")
    write_file(plugin_base, "create_dev_link.sh", CREATE_DEV_LINK)
    dev_link_path = os.path.join(plugin_base, "create_dev_link.sh")
    os.system("chmod +x %s" % dev_link_path)  # lazy..
    os.system(dev_link_path)


CORE = """
import logging
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

DEFAULT_PREFS = {
    "test":"NiNiNi"
}

log = logging.getLogger(__name__)

class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("%(safe_name)s.conf", DEFAULT_PREFS)

    def disable(self):
        pass

    def update(self):
        pass

    @export
    def set_config(self, config):
        \"\"\"Sets the config dictionary\"\"\"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        \"\"\"Returns the config dictionary\"\"\"
        return self.config.config
"""

INIT = """
from deluge.plugins.init import PluginInitBase

class CorePlugin(PluginInitBase):
    def __init__(self, plugin_name):
        from core import Core as _plugin_cls
        self._plugin_cls = _plugin_cls
        super(CorePlugin, self).__init__(plugin_name)

class GtkUIPlugin(PluginInitBase):
    def __init__(self, plugin_name):
        from gtkui import GtkUI as _plugin_cls
        self._plugin_cls = _plugin_cls
        super(GtkUIPlugin, self).__init__(plugin_name)

class WebUIPlugin(PluginInitBase):
    def __init__(self, plugin_name):
        from webui import WebUI as _plugin_cls
        self._plugin_cls = _plugin_cls
        super(WebUIPlugin, self).__init__(plugin_name)
"""


SETUP = """
from setuptools import setup, find_packages

__plugin_name__ = "%(name)s"
__author__ = "%(author_name)s"
__author_email__ = "%(author_email)s"
__version__ = "0.1"
__url__ = "%(url)s"
__license__ = "GPLv3"
__description__ = ""
__long_description__ = \"\"\"\"\"\"
__pkg_data__ = {"deluge.plugins."+__plugin_name__.lower(): ["template/*", "data/*"]}

setup(
    name=__plugin_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    long_description=__long_description__ if __long_description__ else __description__,

    packages=find_packages(),
    namespace_packages = ["deluge", "deluge.plugins"],
    package_data = __pkg_data__,

    entry_points=\"\"\"
    [deluge.plugin.core]
    %%(plugin_name)s = deluge.plugins.%%(plugin_module)s:CorePlugin
    [deluge.plugin.gtkui]
    %%(plugin_name)s = deluge.plugins.%%(plugin_module)s:GtkUIPlugin
    [deluge.plugin.web]
    %%(plugin_name)s = deluge.plugins.%%(plugin_module)s:WebUIPlugin
    \"\"\" %% dict(plugin_name=__plugin_name__, plugin_module=__plugin_name__.lower())
)
"""

COMMON = """

def get_resource(filename):
    import pkg_resources, os
    return pkg_resources.resource_filename("deluge.plugins.%(safe_name)s",
                                           os.path.join("data", filename))
"""

GTKUI = """
from gi.repository import Gtk
import logging

from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

from common import get_resource

log = logging.getLogger(__name__)

class GtkUI(GtkPluginBase):
    def enable(self):
        self.glade = Gtk.glade.XML(get_resource("config.glade"))

        component.get("Preferences").add_page("%(name)s", self.glade.get_widget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)

    def disable(self):
        component.get("Preferences").remove_page("%(name)s")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for %(name)s")
        config = {
            "test":self.glade.get_widget("txt_test").get_text()
        }
        client.%(safe_name)s.set_config(config)

    def on_show_prefs(self):
        client.%(safe_name)s.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.glade.get_widget("txt_test").set_text(config["test"])
"""

GLADE = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE glade-interface SYSTEM "glade-2.0.dtd">
<!--Generated with glade3 3.4.5 on Fri Aug  8 23:34:44 2008 -->
<glade-interface>
  <widget class="GtkWindow" id="window1">
    <child>
      <widget class="GtkHBox" id="prefs_box">
        <property name="visible">True</property>
        <child>
          <widget class="GtkLabel" id="label1">
            <property name="visible">True</property>
            <property name="label" translatable="yes">Test config value:</property>
          </widget>
        </child>
        <child>
          <widget class="GtkEntry" id="txt_test">
            <property name="visible">True</property>
            <property name="can_focus">True</property>
          </widget>
          <packing>
            <property name="position">1</property>
          </packing>
        </child>
      </widget>
    </child>
  </widget>
</glade-interface>
"""

WEBUI = """
import logging
from deluge.ui.client import client
from deluge import component
from deluge.plugins.pluginbase import WebPluginBase

from common import get_resource

log = logging.getLogger(__name__)

class WebUI(WebPluginBase):

    scripts = [get_resource("%(safe_name)s.js")]

    def enable(self):
        pass

    def disable(self):
        pass
"""

DEFAULT_JS = """/*
Script: %(filename)s
    The client-side javascript code for the %(name)s plugin.

Copyright:
    (C) %(author_name)s %(current_year)s <%(author_email)s>

    This file is part of %(name)s and is licensed under GNU General Public License 3.0, or later, with
    the additional special exception to link portions of this program with the OpenSSL library.
    See LICENSE for more details.
*/

%(name)sPlugin = Ext.extend(Deluge.Plugin, {
    constructor: function(config) {
        config = Ext.apply({
            name: "%(name)s"
        }, config);
        %(name)sPlugin.superclass.constructor.call(this, config);
    },

    onDisable: function() {

    },

    onEnable: function() {

    }
});
new %(name)sPlugin();
"""

GPL = """#
# -*- coding: utf-8 -*-#

# Copyright (C) %(current_year)d %(author_name)s <%(author_email)s>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
# Copyright (C) 2010 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of %(name)s and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
"""

NAMESPACE_INIT = """# this is a namespace package
import pkg_resources
pkg_resources.declare_namespace(__name__)
"""

CREATE_DEV_LINK = """#!/bin/bash
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

create_plugin()
