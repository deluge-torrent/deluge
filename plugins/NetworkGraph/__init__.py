# -*- coding: utf-8 -*-
#
# __init__.py
#
# Copyright (C) Marcos Pinto 2007 <markybob@gmail.com>
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
#  statement from all source files in the program, then also delete it here.

plugin_name = "Network Activity Graph"
plugin_author = "Alon Zakai, Zach Tibbitts, Cinar Sahin"
plugin_version = "0.2.1"
plugin_description = _("Network Activity Graph plugin\n\nWritten by Kripkenstein")


def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return NetworkGraph(path, core, interface)

from NetworkGraph.tab_graph import GraphTabManager

import gtk
import deluge

class NetworkGraph:
    def __init__(self, path, core, interface):
        self.parent   = interface
        self.location = path
        self.manager = core
        self.dialog_initialize = True
        self.glade = gtk.glade.XML(path + "/graph_preferences.glade")
        self.dialog = self.glade.get_widget("dialog")
        self.glade.signal_autoconnect({
                                        'on_Reset_Download_released' : self.reset_download,
                                        'on_Reset_Upload_released' : self.reset_upload,
                                        'on_button_cancel_pressed': self.cancel_pressed,
                                        'on_button_ok_pressed': self.ok_pressed
                                        })

        self.config_file = deluge.common.CONFIG_DIR + "/graph.conf"
        self.config = deluge.pref.Preferences(self.config_file, False)
        try:
            self.config.load()
        except IOError:
            # File does not exist
            pass
        
        scrolledWindow = gtk.ScrolledWindow()
        scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        image  = gtk.Image()

        viewport = gtk.Viewport()
        viewport.add(image)
        scrolledWindow.add(viewport)

        image.show()
        viewport.show()
        self.topWidget = scrolledWindow

        self.parentNotebook = self.parent.notebook
#        print "Parent NOTEBOOK:", self.parentNotebook
        self.parentNotebook.append_page(self.topWidget, gtk.Label(_("Graph")))
#        print "My INDEX in parentNoteBook:", self.index
        self.bootupRuns = 3  # This ensures that we pass the resizing phase, with scrollbars, etc.
                                    # So the first time it is viewed, we are all ready
        scrolledWindow.show()
        import pango
        pangoContext = self.parent.window.get_pango_context()
        pangoLayout = pango.Layout(pangoContext)

        self.tab_graph = GraphTabManager(scrolledWindow, image, pangoLayout, self.manager)
        self.update_config()

    def unload(self): # Shutdown is called when the plugin is deactivated
        numPages = self.parentNotebook.get_n_pages()
        for page in range(numPages):
            if self.parentNotebook.get_nth_page(page) == self.topWidget:
                self.parentNotebook.remove_page(page)
                break
        self.config.save(self.config_file)

    def configure(self, window):
        self.dialog_initialize = True
        try:
            if self.config.get("enable_down_line"):
                self.glade.get_widget("Download_Line_Check").set_active(True)
            else:
                self.glade.get_widget("Download_Line_Check").set_active(False)

            if self.config.get("enable_down_fill"):
                self.glade.get_widget("Download_Fill_Check").set_active(True)
            else:
                self.glade.get_widget("Download_Fill_Check").set_active(False)

            if self.config.get("enable_up_line"):
                self.glade.get_widget("Upload_Line_Check").set_active(True)
            else:
                self.glade.get_widget("Upload_Line_Check").set_active(False)

            if self.config.get("enable_up_fill"):
                self.glade.get_widget("Upload_Fill_Check").set_active(True)
            else:
                self.glade.get_widget("Upload_Fill_Check").set_active(False)

            if (self.config.get("line_size") > 0) & (self.config.get("line_size") < 6):
                self.glade.get_widget("Line_Scale").get_adjustment().set_value(self.config.get("line_size"))
            else:
                self.glade.get_widget("Line_Scale").get_adjustment().set_value(2);

            if (self.config.get("length") > 59) & (self.config.get("length") < 3601):
		self.glade.get_widget("History_Scale").get_adjustment().set_value(self.config.get("length"))
	    else:
		self.glade_get_widget("History_Scale").get_adjustment().set_value(60);

            if self.config.get("colors_set"):
                dl_color = self.config.get("down_line_color")
                df_color = self.config.get("down_fill_color")
                ul_color = self.config.get("up_line_color")
                uf_color = self.config.get("up_fill_color")
                self.glade.get_widget("Download_Line").set_color(gtk.gdk.Color(int(dl_color[0]*65535),int(dl_color[1]*65535),int(dl_color[2]*65535)))
                self.glade.get_widget("Download_Line").set_alpha(int(dl_color[3]*65535))
                self.glade.get_widget("Download_Fill").set_color(gtk.gdk.Color(int(df_color[0]*65535),int(df_color[1]*65535),int(df_color[2]*65535)))
                self.glade.get_widget("Download_Fill").set_alpha(int(df_color[3]*65535))
                self.glade.get_widget("Upload_Line").set_color(gtk.gdk.Color(int(ul_color[0]*65535),int(ul_color[1]*65535),int(ul_color[2]*65535)))
                self.glade.get_widget("Upload_Line").set_alpha(int(ul_color[3]*65535))
                self.glade.get_widget("Upload_Fill").set_color(gtk.gdk.Color(int(uf_color[0]*65535),int(uf_color[1]*65535),int(uf_color[2]*65535)))
                self.glade.get_widget("Upload_Fill").set_alpha(int(uf_color[3]*65535))
            else:
                self.glade.get_widget("Download_Line").set_color(gtk.gdk.Color(0,49151,0))
                self.glade.get_widget("Download_Line").set_alpha(65535)
                self.glade.get_widget("Download_Fill").set_color(gtk.gdk.Color(32768,65535,32768))
                self.glade.get_widget("Download_Fill").set_alpha(65535)
                self.glade.get_widget("Upload_Line").set_color(gtk.gdk.Color(0,0,65535))
                self.glade.get_widget("Upload_Line").set_alpha(49151)
                self.glade.get_widget("Upload_Fill").set_color(gtk.gdk.Color(21627,21627,65535))
                self.glade.get_widget("Upload_Fill").set_alpha(32768)

            self.glade.get_widget("Mean_Speed_Check").set_active(self.config.get("mean_selected"))
            self.glade.get_widget("Max_Speed_Check").set_active(self.config.get("max_selected"))
            self.glade.get_widget("Legend_Check").set_active(self.config.get("legend_selected"))

        except:
            self.glade.get_widget("Download_Line_Check").set_active(True)
            self.glade.get_widget("Download_Fill_Check").set_active(True)
            self.glade.get_widget("Upload_Line_Check").set_active(True)
            self.glade.get_widget("Upload_Fill_Check").set_active(True)
            self.glade.get_widget("Mean_Speed_Check").set_active(True)
            self.glade.get_widget("Max_Speed_Check").set_active(True)
            self.glade.get_widget("Download_Line").set_color(gtk.gdk.Color(0,49151,0))
            self.glade.get_widget("Download_Line").set_alpha(65535)
            self.glade.get_widget("Download_Fill").set_color(gtk.gdk.Color(32768,65535,32768))
            self.glade.get_widget("Download_Fill").set_alpha(65535)
            self.glade.get_widget("Upload_Line").set_color(gtk.gdk.Color(0,0,65535))
            self.glade.get_widget("Upload_Line").set_alpha(49151)
            self.glade.get_widget("Upload_Fill").set_color(gtk.gdk.Color(21627,21627,65535))
            self.glade.get_widget("Upload_Fill").set_alpha(32768)
            self.glade.get_widget("Line_Scale").get_adjustment().set_value(4);
	    self.glade.get_widget("History_Scale").get_adjustment().set_value(60);
            self.glade.get_widget("Mean_Speed_Check").set_active(True)
            self.glade.get_widget("Max_Speed_Check").set_active(False)
            self.glade.get_widget("Legend_Check").set_active(True)

        self.dialog_initialize = False
        self.dialog.set_transient_for(window)
        self.dialog.show()

    def update(self):
        if (not self.parentNotebook.get_nth_page(self.parentNotebook.get_current_page()) == \
                self.topWidget\
                or not self.parent.update_interface)\
                and not self.bootupRuns > 0:
            self.tab_graph.update_graph_store()
        self.bootupRuns = max(self.bootupRuns - 1, 0)
        self.tab_graph.update_graph_store()
        self.tab_graph.update_graph_view()

    def update_config(self):
        if self.config.get("exists"):
            if self.config.get("enable_down_line"):
                self.tab_graph.enable_download_line()
            else:
               self.tab_graph.disable_download_line()

            if self.config.get("enable_down_fill"):
                self.tab_graph.enable_download_fill()
            else:
                self.tab_graph.disable_download_fill()

            if self.config.get("enable_up_line"):
                self.tab_graph.enable_upload_line()
            else:
                self.tab_graph.disable_upload_line()

            if self.config.get("enable_up_fill"):
                self.tab_graph.enable_upload_fill()
            else:
                self.tab_graph.disable_upload_fill()


            if self.config.get("down_line_color"):
                self.tab_graph.download_line_color = self.config.get("down_line_color")
            else:
                self.tab_graph.download_line_color = (0,  0.75,0,   1.0)

            if self.config.get("down_fill_color"):
                self.tab_graph.download_fill_color = self.config.get("down_fill_color")
            else:
                self.tab_graph.download_fill_color = (0.5,1,   0.5, 1.0)

            if self.config.get("up_line_color"):
                self.tab_graph.upload_line_color = self.config.get("up_line_color")
            else:
                self.tab_graph.upload_line_color = (0,   0,   1.0,  0.75)

            if self.config.get("up_fill_color"):
                self.tab_graph.upload_fill_color = self.config.get("up_fill_color")
            else:
                self.tab_graph.upload_fill_color = (0.33,0.33,1.0,  0.5)


            if (self.config.get("line_size") > 0) & (self.config.get("line_size") < 6):
                self.tab_graph.line_size = self.config.get("line_size")
            else:
                self.tab_graph.line_size = 4

            if (self.config.get("length") > 59) & (self.config.get("length") < 3601):
                self.tab_graph.length = self.config.get("length")
            else:
                self.tab_graph.length = 60

            if self.config.get("mean_selected"):
                self.tab_graph.enable_mean()
            else:
                self.tab_graph.disable_mean()

            if self.config.get("max_selected"):
                self.tab_graph.enable_max()
            else:
                self.tab_graph.disable_max()

            if self.config.get("legend_selected"):
                self.tab_graph.enable_legend()
            else:
                self.tab_graph.disable_legend()
        else:
            self.tab_graph.enable_download_line()
            self.tab_graph.enable_download_fill()
            self.tab_graph.enable_upload_line()
            self.tab_graph.enable_upload_fill()
            self.tab_graph.download_line_color = (0,  0.75,0,   1.0)
            self.tab_graph.download_fill_color = (0.5,1,   0.5, 1.0)
            self.tab_graph.upload_line_color = (0,   0,   1.0,  0.75)
            self.tab_graph.upload_fill_color = (0.33,0.33,1.0,  0.5)
            self.tab_graph.enable_mean()
            self.tab_graph.enable_legend()
            self.tab_graph.line_size = 4
	    self.tab_graph.length = 60

    def reset_download(self,src):
        self.glade.get_widget("Download_Line_Check").set_active(True)
        self.glade.get_widget("Download_Fill_Check").set_active(True)
        self.glade.get_widget("Download_Line").set_color(gtk.gdk.Color(0,49151,0))
        self.glade.get_widget("Download_Line").set_alpha(65535)
        self.glade.get_widget("Download_Fill").set_color(gtk.gdk.Color(32768,65535,32768))
        self.glade.get_widget("Download_Line").set_,sralpha(65535)

    def reset_upload(self,src):
        self.glade.get_widget("Upload_Line_Check").set_active(True)
        self.glade.get_widget("Upload_Fill_Check").set_active(True)
        self.glade.get_widget("Upload_Line").set_color(gtk.gdk.Color(0,0,65535))
        self.glade.get_widget("Upload_Line").set_alpha(49151)
        self.glade.get_widget("Upload_Fill").set_color(gtk.gdk.Color(21627,21627,65535))
        self.glade.get_widget("Upload_Fill").set_alpha(32768)

    def ok_pressed(self, src):
        self.dialog.hide()
        self.config.set("exists",True)
        self.config.set("enable_down_line",self.glade.get_widget("Download_Line_Check").get_active())
        self.config.set("down_line_color",(self.glade.get_widget("Download_Line").get_color().red/65535.0,\
                                            self.glade.get_widget("Download_Line").get_color().green/65535.0,\
                                            self.glade.get_widget("Download_Line").get_color().blue/65535.0,\
                                            self.glade.get_widget("Download_Line").get_alpha()/65535.0))

        self.config.set("enable_down_fill",self.glade.get_widget("Download_Fill_Check").get_active())
        self.config.set("down_fill_color",(self.glade.get_widget("Download_Fill").get_color().red/65535.0,\
                                            self.glade.get_widget("Download_Fill").get_color().green/65535.0,\
                                            self.glade.get_widget("Download_Fill").get_color().blue/65535.0,\
                                            self.glade.get_widget("Download_Fill").get_alpha()/65535.0))

        self.config.set("enable_up_line",self.glade.get_widget("Upload_Line_Check").get_active())
        self.config.set("up_line_color",(self.glade.get_widget("Upload_Line").get_color().red/65535.0,\
                                        self.glade.get_widget("Upload_Line").get_color().green/65535.0,\
                                        self.glade.get_widget("Upload_Line").get_color().blue/65535.0,\
                                        self.glade.get_widget("Upload_Line").get_alpha()/65535.0))

        self.config.set("enable_up_fill",self.glade.get_widget("Upload_Fill_Check").get_active())
        self.config.set("up_fill_color",(self.glade.get_widget("Upload_Fill").get_color().red/65535.0,\
                                        self.glade.get_widget("Upload_Fill").get_color().green/65535.0,\
                                        self.glade.get_widget("Upload_Fill").get_color().blue/65535.0,\
                                        self.glade.get_widget("Upload_Fill").get_alpha()/65535.0))

        self.config.set("colors_set",True)
        self.config.set("line_size",self.glade.get_widget("Line_Scale").get_adjustment().get_value())
	self.config.set("length",self.glade.get_widget("History_Scale").get_adjustment().get_value())
        self.config.set("mean_selected",self.glade.get_widget("Mean_Speed_Check").get_active())
        self.config.set("max_selected",self.glade.get_widget("Max_Speed_Check").get_active())
        self.config.set("legend_selected",self.glade.get_widget("Legend_Check").get_active())
        self.update_config()

    def cancel_pressed(self, src):
        self.dialog.hide()
