# -*- coding: utf-8 -*-
# Dbus Ipc for experimental web interface
#
# dbus_interface.py
#
# Copyright (C) Martijn Voncken 2007 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception

plugin_name = "Web User interface"
plugin_author = "Martijn Voncken"
plugin_version = "rev."
plugin_description = "A Web based User Interface\n"

import deluge.common
import deluge.pref
from deluge.dialogs import show_popup_warning
from dbus_interface import DbusManager

import gtk
import os
from subprocess import Popen
from md5 import md5
import random
random.seed()

plugin_version += open(os.path.join(os.path.dirname(__file__),'revno')).read()
plugin_description += (
    open(os.path.join(os.path.dirname(__file__),'version')).read())


def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return plugin_WebUi(path, core, interface)

class plugin_WebUi:
    def __init__(self, path, deluge_core, deluge_interface):
        self.path = path
        self.core = deluge_core
        self.interface = deluge_interface
        self.proc = None

        self.config_file = deluge.common.CONFIG_DIR + "/webui.conf"
        self.config = deluge.pref.Preferences(self.config_file, False)
        try:
            self.config.load()
        except IOError:
            # File does not exist
            pass

        if not self.config.get('port'): #ugly way to detect new config file.
            #set default values:
            self.config.set("port", 8112)
            #future->use deluge-core setting for download_dir (if it is set)
            self.config.set("download_dir", os.path.expanduser("~/"))
            self.config.set("torrent_dir", os.path.expanduser("~/"))
            self.config.set("button_style", 2)
            self.config.set("auto_refresh", False)
            self.config.set("auto_refresh_secs", 4)
            self.config.set("template", "deluge")
            self.config.save(self.config_file)

        if not self.config.get("pwd_salt"):
            self.config.set("pwd_salt", "invalid")
            self.config.set("pwd_md5", "invalid")


        self.dbusManager = DbusManager(deluge_core, deluge_interface
            , self.config, self.config_file)

        print dir(self.dbusManager)
        self.start_server()

    def unload(self):
        print 'WebUI:unload..'
        self.kill_server()
        #self.dbusManager.

    def update(self):
        pass

    ## This will be only called if your plugin is configurable
    def configure(self,parent_dialog):
        d = ConfigDialog(self.config,self)
        if d.run() == gtk.RESPONSE_OK:
            d.save_config()
        d.destroy()

    def start_server(self):
        self.kill_server()
        print 'start Webui..'
        path = os.path.dirname(__file__)
        server_bin = path + '/run_webserver'
        port = str(self.config.get('port'))
        self.proc = Popen((server_bin, port),cwd=path)

    def kill_server(self):
        if self.proc:
            print "webserver: kill %i"%self.proc.pid
            os.system("kill %i"%self.proc.pid)
        self.proc = None


class ConfigDialog(gtk.Dialog):
    """
    sorry, can't get used to gui builders.
    from what I read glade is better, but i dont want to invest time in them.
    """
    def __init__(self, config, plugin):
        gtk.Dialog.__init__(self)
        self.config = config
        self.plugin = plugin
        self.vb = gtk.VBox()
        self.set_title(_("WebUi Config"))

        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.templates = [dirname for dirname
            in os.listdir(template_path)
            if os.path.isdir(os.path.join(template_path, dirname))]

        self.port = self.add_widget(_('Port Number'), gtk.SpinButton())
        self.pwd1 = self.add_widget(_('New Password'), gtk.Entry())
        self.pwd2 = self.add_widget(_('New Password(confirm)'), gtk.Entry())
        self.template = self.add_widget(_('Template'), gtk.combo_box_new_text())
        self.button_style = self.add_widget(_('Button Style'),
            gtk.combo_box_new_text())
        self.download_dir = self.add_widget(_('Download Directory'),
            gtk.FileChooserButton(_('Download Directory')))
        self.torrent_dir = self.add_widget(_('Torrent Directory'),
            gtk.FileChooserButton(_('Torrent Directory')))

        self.download_dir.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self.torrent_dir.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self.port.set_range(80, 65536)
        self.port.set_increments(1, 10)
        self.pwd1.set_visibility(False)
        self.pwd2.set_visibility(False)

        for item in self.templates:
            self.template.append_text(item)
        self.button_style
        if not self.config.get("template") in self.templates:
            self.config.set("template","deluge")

        for item in [_('Text and image'), _('Image Only'), _('Text Only')]:
            self.button_style.append_text(item)
        if not self.config.get("button_style"):
            self.config.set("button_style", 2)

        self.port.set_value(int(self.config.get("port")))
        self.template.set_active(
            self.templates.index(self.config.get("template")))
        self.button_style.set_active(self.config.get("button_style"))
        self.torrent_dir.set_filename(self.config.get("torrent_dir"))
        self.download_dir.set_filename(self.config.get("download_dir"))
        self.vbox.pack_start(self.vb, True, True, 0)
        self.vb.show_all()

        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
            ,gtk.STOCK_OK, gtk.RESPONSE_OK)

    def add_widget(self,label,w=None):
        hb = gtk.HBox()
        lbl = gtk.Label(label)
        lbl.set_size_request(200,20)
        hb.pack_start(lbl,False,False, 0)
        hb.pack_start(w,True,True, 0)

        self.vb.pack_start(hb,False,False, 0)
        return w
        self.add_buttons(dgtk.STOCK_CLOSE, dgtk.RESPONSE_CLOSE)

    def save_config(self):
        if self.pwd1.get_text() > '':
            if self.pwd1.get_text() <> self.pwd2.get_text():
                show_popup_warning(self,_("Confirmed Password <> New Password\n"
                    + "Password was not changed"))
            else:
                salt = str(random.getrandbits(500))
                m = md5()
                m.update(salt)
                m.update(unicode(self.pwd1.get_text()))
                self.config.set("pwd_salt", salt)
                self.config.set("pwd_md5", m.digest())

        self.config.set("port", int(self.port.get_value()))
        self.config.set("template", self.template.get_active_text())
        self.config.set("button_style", self.button_style.get_active())
        self.config.set("torrent_dir", self.torrent_dir.get_filename())
        self.config.set("download_dir",self.download_dir.get_filename())
        self.config.save(self.plugin.config_file)
        self.plugin.start_server() #restarts server









