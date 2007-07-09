#
# gtkui_mainwindow.py
#
# Copyright (C) Andrew Resch  2007 <andrewresch@gmail.com> 
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
# any later version.
# 
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with deluge.  If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
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

import logging

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade

# Get the logger
log = logging.getLogger("deluge")

class GtkUIMainWindow:
  def __init__(self, glade_xml):
    self.main_glade = glade_xml
    self.window = self.main_glade.get_widget("main_window")
    
    # Initialize various components of the gtkui
    self.menubar = GtkUIMainWindow_MenuBar(self)
  
  def show(self):
    self.window.show_all()
  
  def hide(self):
    self.window.hide()
    
  def quit(self):
    self.hide()
    gtk.main_quit()
    
class GtkUIMainWindow_MenuBar:
  def __init__(self, mainwindow):
    self.mainwindow = mainwindow
    
    ### Connect Signals ###
    self.mainwindow.main_glade.signal_autoconnect({
      ## File Menu
      "on_addtorrent_menuitem_activate": self.on_addtorrent_menuitem_activate,
      "on_addurl_menuitem_activate": self.on_addurl_menuitem_activate,
      "on_clearcompleted_menuitem_activate": \
                                      self.on_clearcompleted_menuitem_activate,
      "on_quit_menuitem_activate": self.on_quit_menuitem_activate
    })
    
  ### Callbacks ###
  def on_addtorrent_menuitem_activate(self, data=None):
    log.debug("on_addtorrent_menuitem_activate")
  def on_addurl_menuitem_activate(self, data=None):
    log.debug("on_addurl_menuitem_activate")
  def on_clearcompleted_menuitem_activate(self, data=None):
    log.debug("on_clearcompleted_menuitem_activate")
  def on_quit_menuitem_activate(self, data=None):
    log.debug("on_quit_menuitem_activate")
    self.mainwindow.quit()
