"""
Creates an empty plugin and links it from ~/.config/deluge/plugins
This plugin includes the framework for using the preferences dialog

example:
python create_plugin.py --name MyPlugin2 --basepath . --author-name "Your Name" --author-email "yourname@example.com"

"""

from optparse import OptionParser
import os
import deluge.common
parser = OptionParser()
parser.add_option("-n", "--name", dest="name",help="plugin name")
parser.add_option("-p", "--basepath", dest="path",help="base path")
parser.add_option("-a", "--author-name", dest="author_name",help="author name,for the GPL header")
parser.add_option("-e", "--author-email", dest="author_email",help="author email,for the GPL header")
parser.add_option("-u", "--url", dest="url", help="Homepage URL")
parser.add_option("-c", "--config", dest="configdir", help="location of deluge configuration")


(options, args) = parser.parse_args()


def create_plugin():
    if not options.name:
        print "--name is mandatory , use -h for more info"
        return
    if not options.path:
        print "--basepath is mandatory , use -h for more info"
        return
    if not options.author_email:
        print "--author-email is mandatory , use -h for more info"
        return
    if not options.author_email:
        print "--author-name is mandatory , use -h for more info"
        return

    if not options.url:
        options.url = ""

    if not os.path.exists(options.path):
        print "basepath does not exist"
        return

    if not options.configdir:
        options.configdir = deluge.common.get_default_config_dir()

    name = options.name.replace(" ", "_")
    safe_name = name.lower()
    plugin_base = os.path.realpath(os.path.join(options.path, safe_name))
    src = os.path.join(plugin_base, safe_name)
    data_dir = os.path.join(src, "data")

    if os.path.exists(plugin_base):
        print "the directory %s already exists, delete it first" % plugin_base
        return

    def write_file(path, filename, template):
        args = {"author_name":options.author_name,
            "author_email":options.author_email ,
            "name":name,
            "safe_name":safe_name,
            "filename":filename,
            "plugin_base":plugin_base,
            "url": options.url,
            "configdir": options.configdir
        }

        filename = os.path.join(path, filename)
        f = open(filename,"w")
        if filename.endswith(".py"):
            f.write(GPL % args)
        f.write(template % args)
        f.close()

    print "creating folders.."
    os.mkdir(plugin_base)
    os.mkdir(src)
    os.mkdir(data_dir)

    print "creating files.."
    write_file(plugin_base,"setup.py", SETUP)
    write_file(src,"__init__.py", INIT)
    write_file(src,"gtkui.py", GTKUI)
    write_file(src,"webui.py", WEBUI)
    write_file(src,"core.py", CORE)
    write_file(src, "common.py", COMMON)
    write_file(data_dir, "config.glade", GLADE)
    write_file(data_dir, "%s.js" % safe_name, DEFAULT_JS)

    #add an input parameter for this?
    print "building dev-link.."
    write_file(plugin_base,"create_dev_link.sh", CREATE_DEV_LINK)
    dev_link_path = os.path.realpath(os.path.join(plugin_base, "create_dev_link.sh"))
    os.system("chmod +x %s" % dev_link_path) #lazy..
    os.system(dev_link_path)


CORE = """
from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

DEFAULT_PREFS = {
    "test":"NiNiNi"
}

class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("%(safe_name)s.conf", DEFAULT_PREFS)

    def disable(self):
        pass

    def update(self):
        pass

    @export
    def set_config(self, config):
        "sets the config dictionary"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        "returns the config dictionary"
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
from setuptools import setup

__plugin_name__ = "%(name)s"
__author__ = "%(author_name)s"
__author_email__ = "%(author_email)s"
__version__ = "0.1"
__url__ = "%(url)s"
__license__ = "GPLv3"
__description__ = ""
__long_description__ = \"\"\"\"\"\"
__pkg_data__ = {__plugin_name__.lower(): ["template/*", "data/*"]}

setup(
    name=__plugin_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    long_description=__long_description__ if __long_description__ else __description__,

    packages=[__plugin_name__.lower()],
    package_data = __pkg_data__,

    entry_points=\"\"\"
    [deluge.plugin.core]
    %%s = %%s:CorePlugin
    [deluge.plugin.gtkui]
    %%s = %%s:GtkUIPlugin
    [deluge.plugin.webui]
    %%s = %%s:WebUIPlugin
    \"\"\" %% ((__plugin_name__, __plugin_name__.lower())*3)
)
"""

COMMON = """
def get_resource(filename):
    import pkg_resources, os
    return pkg_resources.resource_filename("%(safe_name)s", os.path.join("data", filename))
"""

GTKUI = """
import gtk

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

from common import get_resource

class GtkUI(GtkPluginBase):
    def enable(self):
        self.glade = gtk.glade.XML(get_resource("config.glade"))

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
from deluge.log import LOG as log
from deluge.ui.client import client
from deluge import component
from deluge.plugins.pluginbase import WebPluginBase

from common import get_resource

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
    (C) %(author_name)s 2009 <%(author_email)s>
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3, or (at your option)
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, write to:
        The Free Software Foundation, Inc.,
        51 Franklin Street, Fifth Floor
        Boston, MA  02110-1301, USA.

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.
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
# %(filename)s
#
# Copyright (C) 2009 %(author_name)s <%(author_email)s>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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
"""

CREATE_DEV_LINK = """#!/bin/bash
cd %(plugin_base)s
mkdir temp
export PYTHONPATH=./temp
python setup.py build develop --install-dir ./temp
cp ./temp/%(name)s.egg-link %(configdir)s/plugins
rm -fr ./temp
"""

create_plugin()
