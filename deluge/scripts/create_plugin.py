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
    plugin_base = os.path.realpath(os.path.join(options.path, name))
    src = os.path.join(plugin_base, safe_name)
    template_dir = os.path.join(src,"template")

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
    os.mkdir(os.path.join(src,"data"))
    os.mkdir(template_dir)

    print "creating files.."
    write_file(plugin_base,"setup.py", SETUP)
    write_file(src,"__init__.py", INIT)
    write_file(src,"gtkui.py", GTKUI)
    write_file(src,"webui.py", WEBUI)
    write_file(src,"core.py", CORE)
    write_file(os.path.join(src,"data"),"config.glade", GLADE)
    write_file(template_dir,"default.html", DEFAULT_HTML)

    #add an input parameter for this?
    print "building dev-link.."
    write_file(plugin_base,"create_dev_link.sh", CREATE_DEV_LINK)
    dev_link_path = os.path.realpath(os.path.join(plugin_base, "create_dev_link.sh"))
    os.system("chmod +x %s" % dev_link_path) #lazy..
    os.system(dev_link_path)


CORE = """
import deluge
from deluge.log import LOG as log
from deluge.plugins.corepluginbase import CorePluginBase
from deluge import component
#from deluge.plugins.coreclient import client #1.1 and later only
#client: see http://dev.deluge-torrent.org/wiki/Development/UiClient#Remoteapi

DEFAULT_PREFS = {
    "test":"NiNiNi"
}

class Core(CorePluginBase):

    def enable(self):
        self.config = deluge.configmanager.ConfigManager("%(safe_name)s.conf", DEFAULT_PREFS)

    def disable(self):
        pass

    def export_set_config(self, config):
        "sets the config dictionary"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    def export_get_config(self):
        "returns the config dictionary"
        return self.config.config
"""

INIT = """
from deluge.log import LOG as log

from deluge.plugins.init import PluginBase

class CorePlugin(PluginBase):
    def __init__(self, plugin_api, plugin_name):
        # Load the Core portion of the plugin
        try:
            from core import Core
            self.plugin = Core(plugin_api, plugin_name)
        except Exception, e:
            log.debug("Did not load a Core plugin: %%s", e)

class WebUIPlugin(PluginBase):
    def __init__(self, plugin_api, plugin_name):
        try:
            from webui import WebUI
            self.plugin = WebUI(plugin_api, plugin_name)
        except Exception, e:
            log.debug("Did not load a WebUI plugin: %%s", e)

class GtkUIPlugin(PluginBase):
    def __init__(self, plugin_api, plugin_name):
        # Load the GtkUI portion of the plugin
        try:
            from gtkui import GtkUI
            self.plugin = GtkUI(plugin_api, plugin_name)
        except Exception, e:
            log.debug("Did not load a GtkUI plugin: %%s", e)
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
    long_description=__long_description__,

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

GTKUI = """
from deluge.log import LOG as log
from deluge.ui.client import aclient
import gtk

class GtkUI(object):
    def __init__(self, plugin_api, plugin_name):
        log.debug("Calling %(name)s UI init")
        self.plugin = plugin_api

    def enable(self):
        self.glade = gtk.glade.XML(self.get_resource("config.glade"))

        self.plugin.add_preferences_page("%(name)s", self.glade.get_widget("prefs_box"))
        self.plugin.register_hook("on_apply_prefs", self.on_apply_prefs)
        self.plugin.register_hook("on_show_prefs", self.on_show_prefs)
        self.on_show_prefs()

    def disable(self):
        self.plugin.remove_preferences_page("%(name)s")
        self.plugin.deregister_hook("on_apply_prefs", self.on_apply_prefs)
        self.plugin.deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for %(name)s")
        config = {
            "test":self.glade.get_widget("txt_test").get_text()
        }
        aclient.%(safe_name)s_set_config(None, config)

    def on_show_prefs(self):
        aclient.%(safe_name)s_get_config(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.glade.get_widget("txt_test").set_text(config["test"])

    def get_resource(self, filename):
        import pkg_resources, os
        return pkg_resources.resource_filename("%(safe_name)s", os.path.join("data", filename))
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
import os
from deluge.log import LOG as log
from deluge.ui.client import sclient, aclient
from deluge.plugins.webuipluginbase import WebUIPluginBase
from deluge import component

api = component.get("WebPluginApi")
forms = api.forms

class %(safe_name)s_page:
    @api.deco.deluge_page
    def GET(self, args):
        return api.render.%(safe_name)s.default("parameter1", "parameter2") #push data to templates/default.html

class WebUI(WebUIPluginBase):
    #map url's to classes: [(url,class), ..]
    urls = [('/%(safe_name)s/example', %(safe_name)s_page)]

    def enable(self):
        api.config_page_manager.register('plugins', '%(safe_name)s' ,ConfigForm)

    def disable(self):
        api.config_page_manager.deregister('%(safe_name)s')

class ConfigForm(forms.Form):
    #meta:
    title = _("%(name)s")

    #load/save:
    def initial_data(self):
        return sclient.%(safe_name)s_get_config()

    def save(self, data):
        cfg = dict(data)
        sclient.%(safe_name)s_set_config(cfg)

    #django newforms magic: define config fields:
    test = forms.CharField(label=_("Test config value"))
"""

DEFAULT_HTML = """$def with (value1, value2)
$:render.header(_("Demo1"), '')
<div class="panel">
<h2>Demo:%(name)s</h2>
<pre>
$value1
$value2
</pre>'
</div>
$:render.footer()
"""

GPL = """#
# %(filename)s
#
# Copyright (C) 2008 %(author_name)s <%(author_email)s>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
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
