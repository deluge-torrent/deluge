#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# interface.py
#
# Copyright (C) Zach Tibbitts 2006 <zach@collegegeek.org>
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

import os.path
from itertools import izip

import gettext
import gobject
import gtk
import locale
import pygtk
pygtk.require('2.0')

import core
import common
import dialogs
import dgtk
import ipc_manager
import files
import plugins

class DelugeGTK:
    def __init__(self):
        APP = 'deluge'
        DIR = os.path.join(common.INSTALL_PREFIX, 'share', 'locale')
        locale.setlocale(locale.LC_ALL, '')
        locale.bindtextdomain(APP, DIR)
        locale.textdomain(APP)
        gettext.bindtextdomain(APP, DIR)
        gettext.textdomain(APP)
        gettext.install(APP, DIR)
        
        self.ipc_manager = ipc_manager.Manager(self)
        #Start the Deluge Manager:
        self.manager = core.Manager(common.CLIENT_CODE, common.CLIENT_VERSION, 
            '%s %s'%(common.PROGRAM_NAME, common.PROGRAM_VERSION), common.CONFIG_DIR)
        self.files_tab = files.FilesTabManager(self.manager)
        self.plugins = plugins.PluginManager(self.manager, self)
        self.plugins.add_plugin_dir(common.PLUGIN_DIR)
        if os.path.isdir(os.path.join(common.CONFIG_DIR , 'plugins')):
            self.plugins.add_plugin_dir(os.path.join(common.CONFIG_DIR, 'plugins'))
        self.plugins.scan_for_plugins()
        self.config = self.manager.get_config()
        #Set up the interface:
        self.wtree = gtk.glade.XML(common.get_glade_file("delugegtk.glade"), domain=APP)
        self.window = self.wtree.get_widget("main_window")
        self.toolbar = self.wtree.get_widget("tb_middle")
        self.window.drag_dest_set(gtk.DEST_DEFAULT_ALL,[('text/uri-list', 0, 80)], gtk.gdk.ACTION_COPY) 
        self.window.connect("delete_event", self.close)
        self.window.connect("drag_data_received", self.on_drag_data)
        self.window.connect("window-state-event", self.window_state_event)
        self.window.connect("configure-event", self.window_configure_event)
        self.window.set_title(common.PROGRAM_NAME)
        self.window.set_icon_from_file(common.get_pixmap("deluge32.png"))
        
        # self.notebook is used by plugins
        self.notebook = self.wtree.get_widget("torrent_info")
        self.notebook.connect("switch-page", self.notebook_switch_page)
        
        self.statusbar = self.wtree.get_widget("statusbar")
        
        ## Construct the Interface
        try:
            self.build_tray_icon()
        except AttributeError:
            #python-pygtk is < 2.9
            self.tray_icon = dgtk.StupidTray()
            self.has_tray = False
        else:
            self.has_tray = True
        
        self.build_torrent_table()
        self.build_summary_tab()
        self.build_file_tab()
        self.build_peer_tab()
        self.load_status_icons()

        # Set the Torrent menu bar sub-menu to the same as the right-click Torrent pop-up menu
        self.wtree.get_widget("menu_torrent").set_submenu(self.torrent_menu)
        self.wtree.get_widget("menu_torrent").set_sensitive(False)
        
        self.connect_signals()
        
        try:
            self.load_window_settings()
        except KeyError:
            pass
        
        self.apply_prefs()
        self.load_window_geometry()

        # Boolean used in update method to help check whether gui
        # should be updated and is set by the window_state_event method
        self.is_minimized = False
        
        # Boolean set to true if window is not minimized and is "visible"
        self.update_interface = True
        
    def connect_signals(self):
        self.wtree.signal_autoconnect({
                    ## File Menu
                    "add_torrent": self.add_torrent_clicked,
                    "add_torrent_url": self.add_torrent_url_clicked,
                    "remove_torrent": self.remove_torrent_clicked,
                    "menu_quit": self.quit,
                    ## Edit Menu
                    "pref_clicked": self.show_preferences_dialog_clicked,
                    "plugins_clicked": self.show_plugin_dialog_clicked,
                    ## View Menu
                    "toolbar_toggle": self.toolbar_toggle,
                    "infopane_toggle": self.infopane_toggle,
                    "size_toggle": self.size_toggle,
                    "status_toggle": self.status_toggle,
                    "seeders_toggle": self.seeders_toggle,
                    "peers_toggle": self.peers_toggle,
                    "dl_toggle": self.dl_toggle,
                    "ul_toggle": self.ul_toggle,
                    "eta_toggle": self.eta_toggle,
                    "availability_toggle": self.availability_toggle,
                    "share_toggle": self.share_toggle,
                    ## Help Menu
                    "show_about_dialog": self.show_about_dialog,
                    "launchpad": self.launchpad,
                    ## Toolbar
                    "start_pause": self.start_pause,
                    "update_tracker": self.update_tracker,
                    "clear_finished": self.clear_finished,
                    "queue_up": self.q_torrent_up,
                    "queue_down": self.q_torrent_down
                    })
    
    def notebook_switch_page(self, notebook, page, page_num):
        # Force an update when user changes the notebook tab
        self.update_torrent_info_widget(None, page_num)
    
    def build_tray_icon(self):
        self.tray_icon = gtk.status_icon_new_from_file(common.get_pixmap("deluge32.png"))
        
        self.tray_glade = gtk.glade.XML(common.get_glade_file("tray_menu.glade"), domain='deluge')
        self.tray_menu  = self.tray_glade.get_widget("tray_menu")
        self.tray_glade.signal_autoconnect({
            "quit": self.quit,
            "plugins": self.show_plugin_dialog_clicked,
            "preferences": self.show_preferences_dialog_clicked,
            "add_torrent": self.add_torrent_clicked,
            "clear_finished": self.clear_finished,
            "show_hide_window_toggled": self.show_hide_window_toggled
        })
        
        self.tray_glade.get_widget("download-limit-image").set_from_file(common.get_pixmap('downloading16.png'))
        self.tray_glade.get_widget("upload-limit-image").set_from_file(common.get_pixmap('seeding16.png'))
        self.build_tray_bwsetsubmenu()
        
        self.tray_icon.connect("activate", self.tray_clicked)
        self.tray_icon.connect("popup-menu", self.tray_popup)
        
    def tray_popup(self, status_icon, button, activate_time):
        if self.window.get_property("visible"):
            self.tray_glade.get_widget("show_hide_window").set_active(True)
        else:
            self.tray_glade.get_widget("show_hide_window").set_active(False)
             
        self.tray_menu.popup(None, None, gtk.status_icon_position_menu, 
            button, activate_time, status_icon)
    
    def build_tray_bwsetsubmenu(self):
        # Create the Download speed list sub-menu
        self.submenu_bwdownset = self.build_menu_radio_list(
                self.config.get("tray_downloadspeedlist"), self.tray_setbwdown,
                self.config.get("max_download_speed"), _("KiB/s"), 
                show_notset=True, show_other=True)
        
        # Create the Upload speed list sub-menu
        self.submenu_bwupset = self.build_menu_radio_list(
                self.config.get("tray_uploadspeedlist"), self.tray_setbwup, 
                self.config.get("max_upload_speed"), _("KiB/s"), 
                show_notset=True, show_other=True)
        
        # Add the sub-menus to the tray menu
        self.tray_glade.get_widget("download_limit").set_submenu(self.submenu_bwdownset)
        self.tray_glade.get_widget("upload_limit").set_submenu(self.submenu_bwupset)
        
        # Show the sub-menus for all to see
        self.submenu_bwdownset.show_all()
        self.submenu_bwupset.show_all()

    def build_menu_radio_list(self, value_list, callback, pref_value=None, 
                              suffix=None, show_notset=False, 
                              notset_label=None, notset_lessthan=0, show_other=False, show_activated=False, activated_label=None):
        # Build a menu with radio menu items from a list and connect them to the callback
        # The pref_value is what you would like to test for the default active radio item
        # Setting show_unlimited will include an Unlimited radio item
        if notset_label is None:
            notset_label = _("Unlimited")

        if activated_label is None:
            activated_label = _("Activated")

        menu = gtk.Menu()
        group = None
        if show_activated is False:
            for value in sorted(value_list):
                if suffix != None:
                    menuitem = gtk.RadioMenuItem(group, str(value) + " " + suffix)
                else:
                    menuitem = gtk.RadioMenuItem(group, str(value))
            
                group = menuitem

                if value == pref_value and pref_value != None:
                    menuitem.set_active(True)

                if callback != None:
                    menuitem.connect("toggled", callback)

                menu.append(menuitem)

        if show_activated is True:
            for value in sorted(value_list):
                menuitem = gtk.RadioMenuItem(group, str(activated_label))
            
                group = menuitem

                if value == pref_value and pref_value != None:
                    menuitem.set_active(True)

                if callback != None:
                    menuitem.connect("toggled", callback)

                menu.append(menuitem)

 #       if show_activated is True:
#            for value in sorted(value_list):
  #              menuitem = gtk.RadioMenuItem(group, activated_label)
   #             group = menuitem
#
 #               if value == 1:
  #                  menuitem.set_active(False)
   #             else:
    #                menuitem.set_active(True)
     #           menuitem.connect("toggled", callback)
      #          menu.append(menuitem)

        if show_notset:
            menuitem = gtk.RadioMenuItem(group, notset_label)
            if pref_value < notset_lessthan and pref_value != None:
                menuitem.set_active(True)
            if show_activated and pref_value == 1:
                menuitem.set_active(True)
            menuitem.connect("toggled", callback)
            menu.append(menuitem)
            
        # Add the Other... menuitem
        if show_other is True:
            menuitem = gtk.SeparatorMenuItem()
            menu.append(menuitem)
            menuitem = gtk.MenuItem(_("Other..."))
            menuitem.connect("activate", callback)
            menu.append(menuitem)
                    
        return menu
    
    def tray_setbwdown(self, widget, data=None):
        str_bwdown     = widget.get_children()[0].get_text().rstrip(" "+_("KiB/s"))
        if str_bwdown == _("Unlimited"):
            str_bwdown = -1
        
        if str_bwdown == _("Other..."):
            dialog_glade = gtk.glade.XML(common.get_glade_file("dgtkpopups.glade"))
            speed_dialog = dialog_glade.get_widget("speed_dialog")
            spin_title = dialog_glade.get_widget("spin_title")
            spin_title.set_text(_("Speed:"))
            spin_speed = dialog_glade.get_widget("spin_speed")
            spin_speed.set_value(self.config.get("max_download_speed"))
            spin_speed.select_region(0, -1)
            response = speed_dialog.run()
            if response == 1: # OK Response
                str_bwdown = spin_speed.get_value()
            else:
                speed_dialog.destroy()
                return
            speed_dialog.destroy()
            
        self.config.set("max_download_speed", float(str_bwdown))
        self.apply_prefs()

    def tray_setbwup(self, widget, data=None):
        str_bwup     = widget.get_children()[0].get_text().rstrip(" "+_("KiB/s"))
        if str_bwup == _("Unlimited"):
            str_bwup = -1
        
        if str_bwup == _("Other..."):
            dialog_glade = gtk.glade.XML(common.get_glade_file("dgtkpopups.glade"))
            speed_dialog = dialog_glade.get_widget("speed_dialog")
            spin_speed = dialog_glade.get_widget("spin_speed")
            spin_speed.set_value(self.config.get("max_upload_speed"))
            spin_speed.select_region(0, -1)
            response = speed_dialog.run()
            if response == 1: # OK Response
                str_bwup = spin_speed.get_value()
            else:
                speed_dialog.destroy()
                return
            speed_dialog.destroy()
            
        self.config.set("max_upload_speed", float(str_bwup))
        self.apply_prefs()

    def unlock_tray(self,comingnext):
        entered_pass = gtk.Entry(25)
        entered_pass.set_activates_default(True)
        entered_pass.set_width_chars(25)
        entered_pass.set_visibility(False)
        entered_pass.show()
        tray_lock = gtk.Dialog(title=_("Deluge is locked"), parent=self.window,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        label = gtk.Label(_("Deluge is password protected.\nTo show the Deluge window, please enter your password"))
        label.set_line_wrap(True)
        label.set_justify(gtk.JUSTIFY_CENTER)
        tray_lock.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        tray_lock.set_size_request(400, 200)
        tray_lock.set_default_response(gtk.RESPONSE_ACCEPT)
        tray_lock.vbox.pack_start(label)
        tray_lock.vbox.pack_start(entered_pass)
        tray_lock.show_all()
        if tray_lock.run() == gtk.RESPONSE_ACCEPT:
            if self.config.get("tray_passwd") == entered_pass.get_text():
                if comingnext == "mainwinshow":
                    self.window.show()
                elif comingnext == "prefwinshow":
                    self.show_preferences_dialog()
                elif comingnext == "quitus":
                    self.window.hide()
                    self.shutdown()

        tray_lock.destroy()
        return True

    def load_status_icons(self):
        self.status_icons = \
            {'paused': gtk.gdk.pixbuf_new_from_file(
                           common.get_pixmap("inactive16.png")),
             'seeding': gtk.gdk.pixbuf_new_from_file(
                         common.get_pixmap("seeding16.png")),
             'downloading' : gtk.gdk.pixbuf_new_from_file(
                                 common.get_pixmap("downloading16.png"))}
    
    def list_of_trackers(self,obj=None):
        torrent = self.get_selected_torrent()
        if torrent is not None:
            trackerslist = self.manager.get_trackers(torrent)
            self.show_edit_tracker_dialog(trackerslist)

    def cancel_edit_window(self,arg=None):
        self.edit_window.destroy()

    def accept_edit_window(self,arg=None):
        torrent = self.get_selected_torrent()
        self.textlist = self.textbuffer.get_text(self.textbuffer.get_start_iter(), self.textbuffer.get_end_iter(), include_hidden_chars=False).strip()
        self.manager.replace_trackers(torrent, self.textlist)
        self.edit_window.destroy()

    def show_edit_tracker_dialog(self,list):
        self.textbuffer = gtk.TextBuffer(table=None)
        self.textbuffer.set_text(list)
        self.edit_glade = gtk.glade.XML(common.get_glade_file("edit_trackers.glade"))
        self.edit_list  = self.edit_glade.get_widget("txt_tracker_list")
        self.edit_list.set_buffer(self.textbuffer)
        self.edit_window  = self.edit_glade.get_widget("edittrackers")
        self.edit_window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.edit_window.set_size_request(400, 200)
        self.edit_glade.signal_autoconnect({
                        "cancel_button_clicked": self.cancel_edit_window,
                        "ok_button_clicked": self.accept_edit_window 
                        })

        self.edit_window.show_all() 

        return True

    def tray_clicked(self, status_icon):
        if self.window.get_property("visible"):
            if self.window.is_active():
                self.window.hide()
            else:
                self.window.present()
                # Force UI update as we don't update it while minimized
                self.update()
        else:
            if self.config.get("lock_tray") == True:
                self.unlock_tray("mainwinshow")
            else:
                self.load_window_geometry()
                self.window.show()
                # Force UI update as we don't update it while in tray
                self.update()
    
    def show_hide_window_toggled(self, widget):
        if widget.get_active() and not self.window.get_property("visible"):
            if self.config.get("lock_tray") == True:
                self.unlock_tray("mainwinshow")
            else:
                self.window.show()
        elif not widget.get_active() and self.window.get_property("visible"):
            self.window.hide()

    def build_torrent_table(self):
        ## Create the torrent listview
        self.torrent_view = self.wtree.get_widget("torrent_view")
        self.torrent_glade = gtk.glade.XML(common.get_glade_file("torrent_menu.glade"), domain='deluge')
        self.torrent_menu = self.torrent_glade.get_widget("torrent_menu")        
        self.torrent_glade.signal_autoconnect({
                        "remove_torrent": self.remove_torrent_clicked,
                        "edit_trackers": self.list_of_trackers,
                        "start_pause": self.start_pause,
                        "update_tracker": self.update_tracker,
                        "clear_finished": self.clear_finished,
                        "queue_up": self.q_torrent_up,
                        "queue_down": self.q_torrent_down,
                        "queue_bottom": self.q_to_bottom,
                        "queue_top": self.q_to_top,
                                                })
        self.torrent_menu.connect("focus", self.torrent_menu_focus)
        # unique_ID, Q#, Status Icon, Name, Size, Progress, Message, Seeders, Peers,
        #     DL, UL, ETA, Share
        self.torrent_model = gtk.ListStore(int, gobject.TYPE_UINT, 
            gtk.gdk.Pixbuf, str, gobject.TYPE_UINT64, float, str, int, int, 
            int, int, int, int, gobject.TYPE_UINT64, float, float)
        # Stores unique_ID -> gtk.TreeRowReference's mapping for quick look up
        self.torrent_model_dict = {}

        self.torrent_view.set_model(self.torrent_model)
        self.torrent_view.set_rules_hint(True)
        self.torrent_view.set_reorderable(True)
        self.torrent_view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        def peer(column, cell, model, iter, data):
            c1, c2 = data
            a = int(model.get_value(iter, c1))
            b = int(model.get_value(iter, c2))
            cell.set_property('text', '%d (%d)'%(a, b))
        
        def time(column, cell, model, iter, data):
            time = int(model.get_value(iter, data))
            if time < 0 or time == 0:
                time_str = _("Infinity")
            else:
                time_str = common.ftime(time)
            cell.set_property('text', time_str)
            
        def availability(column, cell, model, iter, data):
            availability_str = float(model.get_value(iter, data))
            cell.set_property('text', "%.3f" % availability_str)
            
        def ratio(column, cell, model, iter, data):
            ratio = float(model.get_value(iter, data))
            if ratio == -1:
                ratio_str = _("Unknown")
            else:
                ratio_str = "%.3f"%ratio
            cell.set_property('text', ratio_str)
        
        ## Initializes the columns for the torrent_view
        (TORRENT_VIEW_COL_UID, TORRENT_VIEW_COL_QUEUE, TORRENT_VIEW_COL_STATUSICON, TORRENT_VIEW_COL_NAME,
        TORRENT_VIEW_COL_SIZE, TORRENT_VIEW_COL_PROGRESS, TORRENT_VIEW_COL_STATUS,
        TORRENT_VIEW_COL_CONNECTED_SEEDS, TORRENT_VIEW_COL_SEEDS,    
        TORRENT_VIEW_COL_CONNECTED_PEERS, TORRENT_VIEW_COL_PEERS, TORRENT_VIEW_COL_DOWNLOAD, 
        TORRENT_VIEW_COL_UPLOAD, TORRENT_VIEW_COL_ETA, 
        TORRENT_VIEW_COL_AVAILABILITY, TORRENT_VIEW_COL_RATIO) = range(16)

        self.queue_column = dgtk.add_text_column(self.torrent_view, "#", TORRENT_VIEW_COL_QUEUE)
        self.name_column = dgtk.add_texticon_column(self.torrent_view, _("Name"), TORRENT_VIEW_COL_STATUSICON, TORRENT_VIEW_COL_NAME)
        self.size_column = dgtk.add_func_column(self.torrent_view, _("Size"), dgtk.cell_data_size, TORRENT_VIEW_COL_SIZE)
        self.status_column = dgtk.add_progress_column(self.torrent_view, _("Status"), TORRENT_VIEW_COL_PROGRESS, TORRENT_VIEW_COL_STATUS)
        self.seed_column = dgtk.add_func_column(self.torrent_view, _("Seeders"), peer, (TORRENT_VIEW_COL_CONNECTED_SEEDS, TORRENT_VIEW_COL_SEEDS))
        self.peer_column = dgtk.add_func_column(self.torrent_view, _("Peers"), peer, (TORRENT_VIEW_COL_CONNECTED_PEERS, TORRENT_VIEW_COL_PEERS))
        self.dl_column = dgtk.add_func_column(self.torrent_view, _("Down Speed"), dgtk.cell_data_speed, TORRENT_VIEW_COL_DOWNLOAD)
        self.ul_column = dgtk.add_func_column(self.torrent_view, _("Up Speed"), dgtk.cell_data_speed, TORRENT_VIEW_COL_UPLOAD)
        self.eta_column = dgtk.add_func_column(self.torrent_view, _("ETA"), time, TORRENT_VIEW_COL_ETA)
        self.availability_column = dgtk.add_func_column(self.torrent_view, _("Availability"), availability, TORRENT_VIEW_COL_AVAILABILITY)
        self.share_column = dgtk.add_func_column(self.torrent_view, _("Ratio"), ratio, TORRENT_VIEW_COL_RATIO)
        
        self.status_column.set_expand(True)
        self.name_column.set_sort_column_id(TORRENT_VIEW_COL_NAME)
        self.seed_column.set_sort_column_id(TORRENT_VIEW_COL_CONNECTED_SEEDS)
        self.peer_column.set_sort_column_id(TORRENT_VIEW_COL_CONNECTED_PEERS)
        
        self.torrent_model.set_sort_column_id(TORRENT_VIEW_COL_QUEUE, 
                                              gtk.SORT_ASCENDING)
        
        try:
            self.torrent_view.get_selection().set_select_function(self.torrent_clicked, full=True)
        except TypeError:
            self.torrent_view.get_selection().set_select_function(self.old_t_click)
        self.torrent_view.connect("button-press-event", self.torrent_view_clicked)

    def torrent_model_append(self, unique_id):
        state = self.manager.get_torrent_state(unique_id)
        iter = self.torrent_model.append(
                   self.get_torrent_state_list(unique_id, state))
        path = self.torrent_model.get_string_from_iter(iter)
        row_ref = gtk.TreeRowReference(self.torrent_model, path)

        self.torrent_model_dict[unique_id] = row_ref

    def torrent_model_remove(self, unique_id):
        row_ref = self.torrent_model_dict[unique_id]
        iter = self.torrent_model.get_iter(row_ref.get_path())
        self.torrent_model.remove(iter)

        del self.torrent_model_dict[unique_id]

    def old_t_click(self, path):
        return self.torrent_clicked(self.torrent_view.get_selection(), self.torrent_model, path, False)
        
    def torrent_clicked(self, selection, model, path, is_selected):
        if is_selected:
            # Torrent is already selected, we don't need to do anything
            return True
        
        self.clear_peer_store()
        self.clear_file_store()
        
        unique_id = model.get_value(model.get_iter(path), 0)
        self.update_torrent_info_widget(unique_id)
        
        return True
    
    def torrent_view_clicked(self, widget, event):
        if event.button == 3:
            data = self.torrent_view.get_path_at_pos(int(event.x), 
                                                     int(event.y))
            if data is None:
                return True
            path, col, cellx, celly = data
            is_selected = self.torrent_view.get_selection().path_is_selected(path)
            if not is_selected:
                self.torrent_view.grab_focus()
                self.torrent_view.set_cursor(path, col, 0)
                
            unique_id = self.torrent_model.get_value(self.torrent_model.get_iter(path), 0)
            # Get the torrent state so we can check if the torrent is paused.
            torrent_state = self.manager.get_torrent_state(unique_id)
            widget = self.torrent_glade.get_widget("menu_pause")
            if torrent_state["is_paused"]:
                widget.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU))
                widget.get_children()[0].set_text(_("Resume"))
            else:
                widget.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_MENU))
                widget.get_children()[0].set_text(_("Pause"))
            
            self.torrent_menu.popup(None, None, None, event.button, 
                                    event.time)
            
            return is_selected
        else:
            return False
    
    def start_pause(self, widget):
        unique_ids = self.get_selected_torrent_rows()
        try:
            for uid in unique_ids:
                self.manager.set_user_pause(uid, not self.manager.is_user_paused(uid))
            
            # We need to force an update so the GUI looks more responsive
            self.update()

        except KeyError:
            pass

    def torrent_menu_focus(self, widget, direction):
        menuitem = self.torrent_glade.get_widget("menu_pause")
        # Check if we are selecting multiple torrents
        if len(self.get_selected_torrent_rows()) > 1:
            menuitem.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_MENU))
            menuitem.get_children()[0].set_text(_("Pause/Resume"))
            return
            
        # Get the selected torrent state so we can check if the torrent is paused.
        unique_id = self.get_selected_torrent()
        if unique_id is None:
            return
        torrent_state = self.manager.get_torrent_state(unique_id)
        if torrent_state["is_paused"]:
            menuitem.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU))
            menuitem.get_children()[0].set_text(_("Resume"))
        else:
            menuitem.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_MENU))
            menuitem.get_children()[0].set_text(_("Pause"))
        
    def build_summary_tab(self):
        #Torrent Summary tab
        # Look into glade's widget prefix function
        self.text_summary_name = self.wtree.get_widget("summary_name")
        self.text_summary_total_size = self.wtree.get_widget("summary_total_size")
        self.text_summary_pieces = self.wtree.get_widget("summary_pieces")
        self.text_summary_availability = self.wtree.get_widget("summary_availability")
        self.text_summary_total_downloaded = self.wtree.get_widget("summary_total_downloaded")
        self.text_summary_total_uploaded = self.wtree.get_widget("summary_total_uploaded")
        self.text_summary_download_speed = self.wtree.get_widget("summary_download_speed")
        self.text_summary_upload_speed = self.wtree.get_widget("summary_upload_speed")
        self.text_summary_seeders = self.wtree.get_widget("summary_seeders")
        self.text_summary_peers = self.wtree.get_widget("summary_peers")
        self.text_summary_percentage_done = self.wtree.get_widget("summary_percentage_done")
        self.text_summary_share_ratio = self.wtree.get_widget("summary_share_ratio")
        self.text_summary_downloaded_this_session = self.wtree.get_widget("summary_downloaded_this_session")
        self.text_summary_uploaded_this_session = self.wtree.get_widget("summary_uploaded_this_session")
        self.text_summary_tracker = self.wtree.get_widget("summary_tracker")
        self.text_summary_tracker_status = self.wtree.get_widget("summary_tracker_status")
        self.text_summary_next_announce = self.wtree.get_widget("summary_next_announce")
        self.text_summary_eta = self.wtree.get_widget("summary_eta")

    def build_peer_tab(self):
        self.peer_view = self.wtree.get_widget("peer_view")
        # IP int, IP string, Client, Percent Complete, Down Speed, Up Speed
        # IP int is for faster sorting
        self.peer_store = gtk.ListStore(gobject.TYPE_UINT, str, str, float, int, int)
        # Stores IP -> gtk.TreeIter's iter mapping for quick look up 
        # in update_torrent_info_widget
        self.peer_store_dict = {}
        
        def percent(column, cell, model, iter, data):
            percent = float(model.get_value(iter, data))
            percent_str = "%.2f%%"%percent
            cell.set_property("text", percent_str)

        self.peer_view.set_model(self.peer_store)
        
        self.peer_ip_column = dgtk.add_text_column(self.peer_view, _("IP Address"), 1)
        self.peer_client_column = dgtk.add_text_column(self.peer_view, _("Client"), 2)
        self.peer_complete_column = dgtk.add_func_column(self.peer_view, _("Percent Complete"), percent, 3)
        self.peer_download_column = dgtk.add_func_column(self.peer_view, _("Down Speed"), dgtk.cell_data_speed, 4)
        self.peer_upload_column = dgtk.add_func_column(self.peer_view, _("Up Speed"), dgtk.cell_data_speed, 5)

        self.peer_ip_column.set_sort_column_id(0)

    def clear_peer_store(self):
        self.peer_store.clear()
        self.peer_store_dict = {}

    def build_file_tab(self):
        self.files_tab.build_file_view(self.wtree.get_widget("file_view"))
    
    def clear_file_store(self):
        self.files_tab.clear_file_store()
        
    def show_about_dialog(self, arg=None):
        dialogs.show_about_dialog()

    def show_preferences_dialog(self):
        active_port = self.manager.get_state()['port']
        preferences_dialog = dialogs.PreferencesDlg(self.config, active_port)
        # Only apply the prefs if the user pressed OK in the prefs dialog
        if preferences_dialog.show() == 1:
            self.apply_prefs()
            self.config.save()

    def show_preferences_dialog_clicked(self, arg=None):
        if self.config.get("lock_tray") == True:
            self.unlock_tray("prefwinshow")
        else:
            self.show_preferences_dialog()
    
    def show_plugin_dialog_clicked(self, arg=None):
        plugin_dialog = dialogs.PluginDlg(self.plugins)
        plugin_dialog.show()
    
    def apply_prefs(self):
        # Show tray icon if necessary
        self.tray_icon.set_visible(self.config.get("enable_system_tray"))
    
        # Update the max_*_speed_bps prefs
        if self.config.get("max_upload_speed") < 0:
            self.config.set("max_upload_speed_bps", -1)
        else:
            self.config.set("max_upload_speed_bps", 
                            int(self.config.get("max_upload_speed") * 1024))

        if self.config.get("max_download_speed") < 0:
            self.config.set("max_download_speed_bps", -1)
        else:
            self.config.set("max_download_speed_bps", 
                            int(self.config.get("max_download_speed") * 1024))
        
        # Update the tray download speed limits
        if self.config.get("max_download_speed") not in self.config.get("tray_downloadspeedlist") and \
                self.config.get("max_download_speed") >= 0:
            # We need to prepend this value and remove the last value in the list
            self.config.get("tray_downloadspeedlist").insert(0, self.config.get("max_download_speed"))
            self.config.get("tray_downloadspeedlist").pop()

        # Do the same for the upload speed limits
        if self.config.get("max_upload_speed") not in self.config.get("tray_uploadspeedlist") and \
                self.config.get("max_upload_speed") >= 0:
            # We need to prepend this value and remove the last value in the list
            self.config.get("tray_uploadspeedlist").insert(0, self.config.get("max_upload_speed"))
            self.config.get("tray_uploadspeedlist").pop()

        # Re-build the tray sub-menu to display the correct active radio item
        self.build_tray_bwsetsubmenu()
        
        # Apply the preferences in the core
        self.manager.apply_prefs()
        self.manager.pe_settings(self.config.get("encout_state"), 
            self.config.get("encin_state"), self.config.get("enclevel_type"), 
                self.config.get("pref_rc4"))
        self.manager.proxy_settings(self.config.get("proxy_hostname"), 
            self.config.get("proxy_username"), self.config.get("proxy_password"), 
                int(self.config.get("proxy_port")), self.config.get("proxy_type"), 
                    self.config.get("peer_proxy"), self.config.get("tracker_proxy"), 
                        self.config.get("dht_proxy"))

    def get_message_from_state(self, torrent_state):
        state = torrent_state['state']
        is_paused = torrent_state['is_paused']
        progress = torrent_state['progress']
        progress = '%d%%'%int(progress * 100)
        if is_paused:
            message = _("Paused %s")%progress
        else:
            try:
                message = core.STATE_MESSAGES[state]
                if state in (1, 3, 4, 7):
                    message = '%s %s'%(message, progress)
            except IndexError:
                message = ''
        return message
    
    # UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, 
    # Share
    def get_torrent_state_list(self, unique_id, state):
        queue = state['queue_pos']
        name = state['name']
        size = state['total_wanted']
        progress = float(state['progress'] * 100)
        message = self.get_message_from_state(state)
        availability = state['distributed_copies']
        share = float(self.calc_share_ratio(unique_id, state))

        # setting after initial paused state ensures first change gets updated
        if state["is_paused"]:
            # Update stats to pause state immediately so interface does not
            # need to keep updating when paused
            seeds = seeds_t = peers = peers_t = dl_speed = ul_speed = eta = 0
            # Set status icon as pause
            status_icon = self.status_icons['paused']
        else:
            seeds = int(state['num_seeds'])
            seeds_t = int(state['total_seeds'])
            peers = int(state['num_peers'])
            peers_t = int(state['total_peers'])
            dl_speed = int(state['download_rate'])
            ul_speed = int(state['upload_rate'])
            try:
                eta = common.get_eta(size, state["total_wanted_done"], 
                                     dl_speed)
            except ZeroDivisionError:
                eta = 0
            # Set the appropriate status icon
            if state["is_seed"]:
                status_icon = self.status_icons['seeding']
            else:
                status_icon = self.status_icons['downloading']
    
        rlist =  [int(unique_id), queue, status_icon, name, size, progress, 
                  message, seeds, seeds_t, peers, peers_t, dl_speed, ul_speed, 
                  eta, availability, share]

        return rlist
    
    ## Start the timer that updates the interface
    def start(self, start_in_tray=False, cmd_line_torrents=None):
        if cmd_line_torrents is None:
            cmd_line_torrents = []
        
        if not(start_in_tray and self.config.get("enable_system_tray") and 
               self.has_tray) and not self.window.get_property("visible"):
            print "Showing window"
            self.window.show()
        
        ## add torrents in manager to interface
        for unique_id in self.manager.get_unique_IDs():
            self.torrent_model_append(unique_id)
            
        for torrent_file in cmd_line_torrents:
            self.interactive_add_torrent(torrent_file)
        
        # Load plugins after we showed main window (if not started in tray)
        self.load_plugins()
        
        # Call update now so everything is up-to-date when the window gains 
        # focus on startup
        self.update()
        
        gobject.timeout_add(1000, self.update)
        try:
            gtk.main()
        except KeyboardInterrupt:
            self.manager.quit()

    def load_plugins(self):
        enable_plugins = self.config.get('enabled_plugins').split(':')
        for plugin in enable_plugins:
            try:
                self.plugins.enable_plugin(plugin)
            except KeyError:
                pass

    ## Call via a timer to update the interface
    def update(self):
        # We need to apply the queue changes
        self.manager.apply_queue()
        
        self.update_interface = self.window.get_property("visible") and not self.is_minimized
        
        # Handle the events
        try:
            self.manager.handle_events()
        except core.StorageMoveFailed, e:
            print "StorageMoveFailed", e
            dialogs.show_popup_warning(self.window, _("You cannot move torrent to a different partition.  Please fix your preferences"))
        
        # Make sure that the interface still exists
        try:
            tab = self.wtree.get_widget("torrent_info").get_current_page()
        except AttributeError:
            return False
        
        # Update Statusbar and Tray Tips
        self.update_statusbar_and_tray()

        #Update any active plugins
        self.plugins.update_active_plugins()
        
        # only update gui if it's needed
        if self.update_interface:
            # Put the generated message into the statusbar
            # This gives plugins a chance to write to the 
            # statusbar if they want
            self.statusbar.pop(1)
            self.statusbar.push(1, self.statusbar_temp_msg)
            
            #Torrent List
            itr = self.torrent_model.get_iter_first()
            
            # Disable torrent options if there are no torrents
            self.wtree.get_widget("menu_torrent").set_sensitive(itr is not None)
            self.wtree.get_widget("toolbutton_remove").set_sensitive(itr is not None)
            self.wtree.get_widget("toolbutton_pause").set_sensitive(itr is not None)
            self.wtree.get_widget("toolbutton_up").set_sensitive(itr is not None)
            self.wtree.get_widget("toolbutton_down").set_sensitive(itr is not None)
        
            if itr is None:
                return True
            
            while itr is not None:
                unique_id = self.torrent_model.get_value(itr, 0)
                
                if unique_id in self.manager.removed_unique_ids:
                    selected_unique_id = self.get_selected_torrent()
                    # If currently selected torrent was complete and so 
                    # removed clear details pane
                    if selected_unique_id == unique_id:
                        self.clear_details_pane()
                    
                    next = self.torrent_model.iter_next(itr)
                    self.torrent_model.remove(itr)
                    itr = self.torrent_model.get_iter_first()
                    if itr is None:
                        return True
                    itr = next
                    
                    del self.manager.removed_unique_ids[unique_id]
                    continue
                    
                # self.torrent_model holds previous state of the torrent.
                # We can check by icon was it paused or not.
                previosly_paused = self.torrent_model.get_value(itr, 2) == \
                                       self.status_icons['paused']
                state = self.manager.get_torrent_state(unique_id)
                if previosly_paused and state['is_paused']:
                    # For previosly and still paused torrents update only 
                    # queue pos and selected files size, all the rest 
                    # columns are unchanged for them.
                    dgtk.update_store(self.torrent_model, itr, (1, 4), 
                                      (state['queue_pos'], 
                                       state['total_wanted']))
                else:
                    tlist = self.get_torrent_state_list(unique_id, state)
                    dgtk.update_store(self.torrent_model, itr, 
                                      xrange(len(tlist)), tlist)
                        
                itr = self.torrent_model.iter_next(itr)
            
            # Disable moving top torrents up or bottom torrents down
            top_torrents_selected = True
            bottom_torrents_selected = True
            
            torrent_selection = self.torrent_view.get_selection()
            selection_count = torrent_selection.count_selected_rows()
            
            # If no torrent is selected, select the first torrent:
            if selection_count == 0:
                torrent_selection.select_path("0")
                selection_count = 1
            
            for i in xrange(selection_count):
                if not torrent_selection.path_is_selected(i):
                    top_torrents_selected = False
            
                if not torrent_selection.path_is_selected(len(self.torrent_model) - 1 - i):
                    bottom_torrents_selected = False
            
            self.torrent_glade.get_widget("menu_queue_top").set_sensitive(not top_torrents_selected)
            self.torrent_glade.get_widget("menu_queue_up").set_sensitive(not top_torrents_selected)
            self.torrent_glade.get_widget("menu_queue_down").set_sensitive(not bottom_torrents_selected)
            self.torrent_glade.get_widget("menu_queue_bottom").set_sensitive(not bottom_torrents_selected)
            self.wtree.get_widget("toolbutton_up").set_sensitive(not top_torrents_selected)
            self.wtree.get_widget("toolbutton_down").set_sensitive(not bottom_torrents_selected)
            
            unique_id = None
            if selection_count == 1:
                unique_id = self.get_selected_torrent()
                self.update_torrent_info_widget(unique_id)
            else: # selection_count > 1
                self.clear_details_pane()
                
                # Update tool buttons below based on the first selected torrent's state
                path = torrent_selection.get_selected_rows()[1][0]
                unique_id = self.torrent_model.get_value(self.torrent_model.get_iter(path), 0)
            
            if self.manager.get_torrent_state(unique_id)["is_paused"]:
                self.wtree.get_widget("toolbutton_pause").set_stock_id(gtk.STOCK_MEDIA_PLAY)
                self.wtree.get_widget("toolbutton_pause").set_label(_("Resume"))
            else:
                self.wtree.get_widget("toolbutton_pause").set_stock_id(gtk.STOCK_MEDIA_PAUSE)
                self.wtree.get_widget("toolbutton_pause").set_label(_("Pause"))
        return True
            
    def update_statusbar_and_tray(self):
        core_state = self.manager.get_state()
        connections = core_state['num_peers']
        if self.config.get("max_connections") < 0 :
            max_connections = _("Unlimited")
        else:
            max_connections = int(self.config.get("max_connections"))
        dlspeed = common.fspeed(core_state['download_rate'])
        ulspeed = common.fspeed(core_state['upload_rate'])
        if self.config.get("max_download_speed") < 0:
            dlspeed_max = _("Unlimited")
        else:
            dlspeed_max = common.fspeed(self.config.get("max_download_speed_bps"))
        if self.config.get("max_upload_speed") < 0:
            ulspeed_max = _("Unlimited")
        else:
            ulspeed_max = common.fspeed(self.config.get("max_upload_speed_bps"))
        
        # Use self.statusbar_temp_msg instance var to allow plugins access it
        self.statusbar_temp_msg = '%s: %s (%s)  %s: %s (%s)  %s: %s (%s)'%(
            _("Connections"), connections, max_connections, _("Down Speed"), 
            dlspeed, dlspeed_max, _("Up Speed"), ulspeed, ulspeed_max)
        
        if 'DHT_nodes' in core_state:
            dht_peers = core_state['DHT_nodes']
            if dht_peers == -1:
                dht_peers = '?'
            else:
                dht_peers = str(dht_peers)
            self.statusbar_temp_msg = self.statusbar_temp_msg + \
                                      '   [' + _("DHT") + ': %s]'%(dht_peers)
        
        msg = '%s\n%s: %s (%s)\n%s: %s (%s)\n%s: %s (%s)' % (
            _("Deluge Bittorrent Client"), _("Connections"), connections, 
            max_connections, _("Down Speed"), dlspeed, dlspeed_max, 
            _("Up Speed"), ulspeed, ulspeed_max)
        
        self.tray_icon.set_tooltip(msg)
        
    def update_torrent_info_widget(self, unique_id=None, page_num=None):
        # Usually we don't need to pass unique_id, but there are a special
        # cases like with self.torrent_clicked() and because of them we have
        # unique_id param
        if unique_id is None:
            unique_id = self.get_selected_torrent()
        # If no torrents added
        if unique_id is None:
            return
        # page_num is to force update info when user just changes tab
        if page_num is None:
            page_num = self.wtree.get_widget("torrent_info").get_current_page()
        
        if page_num == 0: # Details
            state = self.manager.get_torrent_state(unique_id)

            # Update selected files size, tracker, tracker status and next 
            # announce no matter what status of the torrent is
            self.text_summary_total_size.set_text(common.fsize(state["total_wanted"]))
            self.text_summary_tracker.set_text(str(state["tracker"]))
            # At this time we still may not receive EVENT_TRACKER so there
            # could be no tracker_status yet.
            if "tracker_status" in state:
                self.text_summary_tracker_status.set_text(state["tracker_status"])
            self.text_summary_next_announce.set_text(str(state["next_announce"]))
            
            just_paused = False
            if state['is_paused']:
                # Take a notice about " " space on the end, it's like a sign
                # to decide was this torrent already paused before we get here
                # or not. It's to don't add any instance variable for just
                # this specific check and to keep instance clearer.
                if self.text_summary_seeders.get_text() != "0 (0) ":
                    # Selected torrent just paused, zero data now and don't 
                    # update it anymore on each update()
                    state['num_seeds'] = state['total_seeds'] = \
                        state['num_peers'] = state['total_peers'] = \
                        state['download_rate'] = state['upload_rate'] = 0
                    just_paused = True
                else:
                    # If we already updated paused torrent - do nothing more
                    return
            
            self.wtree.get_widget("summary_name").set_text(state['name'])
            self.text_summary_pieces.set_text('%s x %s' % \
                (state["num_pieces"], common.fsize(state["piece_length"])))
            self.text_summary_availability.set_text('%.3f' % state["distributed_copies"])
            self.text_summary_total_downloaded.set_text(common.fsize(state["total_done"]) \
                + " (" + common.fsize(state["total_download"]) + ")")
            self.text_summary_total_uploaded.set_text(common.fsize(self.manager.unique_IDs\
                [unique_id].uploaded_memory + state["total_payload_upload"]) + \
                    " (" + common.fsize(state["total_upload"]) + ")")
            self.text_summary_download_speed.set_text(common.fspeed(state["download_rate"]))
            self.text_summary_upload_speed.set_text(common.fspeed(state["upload_rate"]))
            self.text_summary_seeders.set_text(common.fseed(state) + 
                                               (just_paused and " " or ""))
            self.text_summary_peers.set_text(common.fpeer(state))
            self.wtree.get_widget("progressbar").set_fraction(float(state['progress']))
            self.wtree.get_widget("progressbar").set_text(common.fpcnt(state["progress"]))
            self.text_summary_eta.set_text(common.estimate_eta(state))
            self.text_summary_share_ratio.set_text('%.3f'%(self.calc_share_ratio(unique_id, state)))
        elif page_num == 1: # Peers
            new_peer_info = self.manager.get_torrent_peer_info(unique_id)
            new_ips = set()
            
            for peer in new_peer_info:
                # Update peers already in peers list
                if peer['ip'] in self.peer_store_dict:
                    iter = self.peer_store_dict[peer['ip']]

                    dgtk.update_store(self.peer_store, iter, (3, 4, 5),
                                      (round(peer["peer_has"], 2),
                                       peer["download_speed"],
                                       peer["upload_speed"]))
                
                if peer['client'] != "":
                    new_ips.add(peer['ip'])
                    
                    # Add new peers
                    if peer['ip'] not in self.peer_store_dict:
                        # convert IP to int for sorting purposes
                        ip_int = sum([int(byte) << shift
                                         for byte, shift in 
                                             izip(peer["ip"].split("."), 
                                                  (24, 16, 8, 0))])

                        iter = self.peer_store.append([ip_int, peer["ip"],
                                   unicode(peer["client"], "latin-1"),
                                   round(peer["peer_has"], 2),
                                   peer["download_speed"],
                                   peer["upload_speed"]])

                        self.peer_store_dict[peer['ip']] = iter
            
            # Remove peers that no longer exist in new_ips
            for ip in set(self.peer_store_dict.keys()).difference(new_ips):
                self.peer_store.remove(self.peer_store_dict[ip])
                del self.peer_store_dict[ip]
        elif page_num == 2: # Files
            # Fill self.file_store with files only once and only when we click to
            # Files tab or it's already open
            self.files_tab.set_unique_id(unique_id)
            self.files_tab.prepare_file_store()
            self.files_tab.update_file_store()
    
    def calc_share_ratio(self, unique_id, torrent_state):
        r = float(self.manager.calc_ratio(unique_id, torrent_state))
        return r
    
    # Return the id of the last single selected torrent
    def get_selected_torrent(self):
        try:
            if self.torrent_view.get_selection().count_selected_rows() == 1:
                selected_path = self.torrent_view.get_selection().\
                                    get_selected_rows()[1][0]
                selected_torrent = self.torrent_model.get_value(self.torrent_model.get_iter(selected_path), 0)
                return selected_torrent
        except (TypeError, ValueError):
            pass
        
        return None
            
    # Return a list of ids of the selected torrents
    def get_selected_torrent_rows(self):
        selected_ids = []
        selected_paths = self.torrent_view.get_selection().get_selected_rows()[1]
        
        try:
            for path in selected_paths:
                selected_ids.append(self.torrent_model.get_value(self.torrent_model.get_iter(path), 0))
            return selected_ids
        except ValueError:
            return None
    
    def on_drag_data(self, widget, drag_context, x, y, selection_data, info, timestamp):
        import urllib
    
        uri_split = selection_data.data.strip().split()
        for uri in uri_split:
            path = urllib.url2pathname(uri).strip('\r\n\x00')
            if path.startswith('file:\\\\\\'):
                path = path[8:]
            elif path.startswith('file://'):
                path = path[7:]
            elif path.startswith('file:'):
                path = path[5:]
            if path.endswith('.torrent'):
                self.interactive_add_torrent(path)
                
    def interactive_add_torrent_url(self, url):
        if url:
            filename = common.fetch_url(url)
            if filename:
                self.interactive_add_torrent(filename)
        
    def interactive_add_torrent(self, torrent):
        if self.config.get('use_default_dir'):
            path = self.config.get('default_download_path')
        else:
            path = dialogs.show_directory_chooser_dialog(self.window)
            if path is None:
                return
            
        try:
            dumped_torrent = self.manager.dump_torrent_file_info(torrent)
            if self.config.get('enable_files_dialog') and \
               len(dumped_torrent) > 1:
                files_dialog = dialogs.FilesDlg(dumped_torrent)
                if files_dialog.show() == 1:
                    unique_id = self.manager.add_torrent(torrent, path, 
                                    self.config.get('use_compact_storage'))
                    self.manager.prioritize_files(unique_id, 
                        files_dialog.get_priorities())
                else:
                    return
            else:
                unique_id = self.manager.add_torrent(torrent, path, 
                                self.config.get('use_compact_storage'))
        except core.InvalidEncodingError, e:
            print "InvalidEncodingError", e
            dialogs.show_popup_warning(self.window, _("An error occured while trying to add the torrent. It's possible your .torrent file is corrupted."))
        except core.DuplicateTorrentError, e:
            for unique_id in self.manager.unique_IDs:
                is_duplicate = self.manager.test_duplicate(torrent, unique_id)
                if is_duplicate:
                    break
            if is_duplicate:
                merge_dialog = dialogs.MergeDlg()
                if merge_dialog.show() == 1:
                    new_trackers_as_list = self.manager.dump_trackers(torrent).replace(' ','').splitlines(True)
                    original_trackers_as_list = self.manager.get_trackers(unique_id).replace(' ','').splitlines(True)
                    for index in xrange(len(new_trackers_as_list)):
                        if original_trackers_as_list.count(new_trackers_as_list[index]) == 0:
                            original_trackers_as_list.append(new_trackers_as_list[index])
                    merged_trackers_as_string = ''.join([original_trackers_as_list[index] for \
                        index in xrange(len(original_trackers_as_list))])
                    self.manager.replace_trackers(unique_id, merged_trackers_as_string)
            else:
                dialogs.show_popup_warning(self.window, _("Unknown duplicate torrent error."))
        except core.InsufficientFreeSpaceError, e:
            nice_need = common.fsize(e.needed_space)
            nice_free = common.fsize(e.free_space)
            dialogs.show_popup_warning(self.window, _("There is not enough free disk space to complete your download.") + "\n" + \
                                                        _("Space Needed:") + " " + nice_need + "\n" + \
                                                        _("Available Space:") + " " + nice_free)
        else:
            self.torrent_model_append(unique_id)
            
    def launchpad(self, obj=None):
        common.open_url_in_browser('https://translations.launchpad.net/deluge/trunk/+pots/deluge')
            
    def add_torrent_clicked(self, obj=None):
        torrent = dialogs.show_file_open_dialog()
        if torrent is not None:
            for single in torrent:
                self.interactive_add_torrent(single)

    def add_torrent_url_clicked(self, obj=None):
        dlg = gtk.Dialog(title=_("Add torrent from URL"), parent=self.window,
            buttons=(gtk.STOCK_CANCEL, 0, gtk.STOCK_OK, 1))
        dlg.set_icon_from_file(common.get_pixmap("deluge32.png"))
        
        label = gtk.Label(_("Enter the URL of the .torrent to download"))
        entry = gtk.Entry()
        dlg.vbox.pack_start(label)
        dlg.vbox.pack_start(entry)
        clip = gtk.clipboard_get(selection='PRIMARY')
        text = clip.wait_for_text()
        if text:
            text = text.strip()
            if common.is_url(text):
                entry.set_text(text)
        dlg.show_all()
        result = dlg.run()
        url = entry.get_text()
        dlg.destroy()
        
        if result == 1:
            self.interactive_add_torrent_url(url) 

    def remove_torrent_clicked(self, obj=None):
        glade     = gtk.glade.XML(common.get_glade_file("dgtkpopups.glade"), domain='deluge')
        asker     = glade.get_widget("remove_torrent_dlg")
        
        asker.set_icon_from_file(common.get_pixmap("deluge32.png"))

        warning   =  glade.get_widget("warning")
        warning.set_text(" ")

        torrent_also = glade.get_widget("torrent_also")
        data_also  =  glade.get_widget("data_also")
        data_also.connect("toggled", self.remove_toggle_warning, warning)

        response = asker.run()
        asker.destroy()
        if response == 1:
            self.clear_details_pane()
            
            unique_ids = self.get_selected_torrent_rows()
            
            for unique_id in unique_ids:
                self.manager.remove_torrent(unique_id, data_also.get_active(),
                                            torrent_also.get_active())
                self.torrent_model_remove(unique_id)
            
            self.update()
    
    def clear_details_pane(self):
        self.wtree.get_widget("progressbar").set_text("")
        self.wtree.get_widget("summary_name").set_text("")
        self.text_summary_total_size.set_text("")
        self.text_summary_pieces.set_text("")
        self.text_summary_availability.set_text("")
        self.text_summary_total_downloaded.set_text("")
        self.text_summary_total_uploaded.set_text("")
        self.text_summary_download_speed.set_text("")
        self.text_summary_upload_speed.set_text("")
        self.text_summary_seeders.set_text("")
        self.text_summary_peers.set_text("")
        self.wtree.get_widget("progressbar").set_fraction(0.0)
        self.text_summary_share_ratio.set_text("")
        self.text_summary_tracker.set_text("")
        self.text_summary_tracker_status.set_text("")
        self.text_summary_next_announce.set_text("")
        self.text_summary_eta.set_text("")
        self.clear_peer_store()
        self.clear_file_store()

    def remove_toggle_warning(self, args, warning):
        if not args.get_active():
            warning.set_text(" ")
        else:
            warning.set_markup("<i>" + _("Warning - all downloaded files for this torrent will be deleted!") + "</i>")
        return False

    def update_tracker(self, obj=None):
        torrent = self.get_selected_torrent()
        if torrent is not None:
            self.manager.update_tracker(torrent)
    
    def clear_finished(self, obj=None):
        print "Clearing completed torrents"
        self.manager.clear_completed()
        self.update()
    
    def q_torrent_up(self, obj=None):
        for torrent in self.get_selected_torrent_rows():
            self.manager.queue_up(torrent)
        self.update()

    def q_torrent_down(self, obj=None):
        for torrent in reversed(self.get_selected_torrent_rows()):
            self.manager.queue_down(torrent)
        self.update()

    def q_to_bottom(self, widget):
        for torrent in self.get_selected_torrent_rows():
            self.manager.queue_bottom(torrent)
        self.update()

    def q_to_top(self, widget):
        for torrent in reversed(self.get_selected_torrent_rows()):
            self.manager.queue_top(torrent)
        self.update()
    
    def toolbar_toggle(self, widget):
        if widget.get_active():
            self.wtree.get_widget("tb_left").show()
            self.wtree.get_widget("tb_middle").show()
            self.wtree.get_widget("tb_right").show()
        else:
            self.wtree.get_widget("tb_left").hide()
            self.wtree.get_widget("tb_middle").hide()
            self.wtree.get_widget("tb_right").hide()
    
    def infopane_toggle(self, widget):
        if widget.get_active():
            self.wtree.get_widget("torrent_info").show()
        else:
            self.wtree.get_widget("torrent_info").hide()
        
    def size_toggle(self, obj):
        self.size_column.set_visible(obj.get_active())
            
    
    def status_toggle(self, obj):
        self.status_column.set_visible(obj.get_active())
    
    def seeders_toggle(self, obj):
        self.seed_column.set_visible(obj.get_active())
    
    def peers_toggle(self, obj):
        self.peer_column.set_visible(obj.get_active())
    
    def dl_toggle(self, obj):
        self.dl_column.set_visible(obj.get_active())
    
    def ul_toggle(self, obj):
        self.ul_column.set_visible(obj.get_active())
    
    def eta_toggle(self, obj):
        self.eta_column.set_visible(obj.get_active())
    
    def availability_toggle(self, obj):
        self.availability_column.set_visible(obj.get_active())
        
    def share_toggle(self, obj):
        self.share_column.set_visible(obj.get_active())
        
    def load_window_settings(self):
        self.wtree.get_widget("chk_infopane").set_active(self.config.get("show_infopane"))
        self.wtree.get_widget("chk_toolbar").set_active(self.config.get("show_toolbar"))
        self.wtree.get_widget("chk_size").set_active(self.config.get("show_size"))
        self.wtree.get_widget("chk_status").set_active(self.config.get("show_status"))
        self.wtree.get_widget("chk_seed").set_active(self.config.get("show_seeders"))
        self.wtree.get_widget("chk_peer").set_active(self.config.get("show_peers"))
        self.wtree.get_widget("chk_download").set_active(self.config.get("show_dl"))
        self.wtree.get_widget("chk_upload").set_active(self.config.get("show_ul"))
        self.wtree.get_widget("chk_eta").set_active(self.config.get("show_eta"))
        self.wtree.get_widget("chk_availability").set_active(self.config.get("show_availability"))
        self.wtree.get_widget("chk_ratio").set_active(self.config.get("show_share"))
        self.wtree.get_widget("vpaned1").set_position(self.config.get("window_height") - self.config.get("window_pane_position"))
    
    def save_window_settings(self):
        self.config.set("show_infopane", self.wtree.get_widget("chk_infopane").get_active())
        self.config.set("show_toolbar", self.wtree.get_widget("chk_toolbar").get_active())
        self.config.set("show_size", self.size_column.get_visible())
        self.config.set("show_status", self.status_column.get_visible())
        self.config.set("show_seeders", self.seed_column.get_visible())
        self.config.set("show_peers", self.peer_column.get_visible())
        self.config.set("show_dl", self.dl_column.get_visible())
        self.config.set("show_ul", self.ul_column.get_visible())
        self.config.set("show_eta", self.eta_column.get_visible())
        self.config.set("show_availability", self.availability_column.get_visible())
        self.config.set("show_share", self.share_column.get_visible())
        self.config.set("window_pane_position", self.config.get("window_height") - self.wtree.get_widget("vpaned1").get_position())
    
    def window_configure_event(self, widget, event):
        if self.config.get("window_maximized") == False:
            self.config.set("window_x_pos", self.window.get_position()[0])
            self.config.set("window_y_pos", self.window.get_position()[1])
            self.config.set("window_width", event.width)
            self.config.set("window_height", event.height)

    def window_state_event(self, widget, event):
        if event.changed_mask & gtk.gdk.WINDOW_STATE_MAXIMIZED:
            if event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
                self.config.set("window_maximized", True)
            else:
                self.config.set("window_maximized", False)
        if event.changed_mask & gtk.gdk.WINDOW_STATE_ICONIFIED:
            if event.new_window_state & gtk.gdk.WINDOW_STATE_ICONIFIED:
                self.is_minimized = True
            else:
                self.is_minimized = False
                # Force UI update as we don't update it while minimized
                self.update()
        return False


    def load_window_geometry(self):
        x = self.config.get('window_x_pos')
        y = self.config.get('window_y_pos')
        w = self.config.get('window_width')
        h = self.config.get('window_height')
        self.window.move(x, y)
        self.window.resize(w, h)
        if self.config.get("window_maximized") == True:
            self.window.maximize()

    def close(self, widget, event):
        if self.config.get("close_to_tray") and self.config.get("enable_system_tray") and self.has_tray:
            self.window.hide()
            return True
        else:
            self.quit()
        
    def quit(self, widget=None):
        if self.window.get_property("visible"):
            self.window.hide()
            self.shutdown()
        else:
            if self.config.get("lock_tray") == True:
                self.unlock_tray("quitus")
            else:
                self.window.hide()
                self.shutdown()
    
    def shutdown(self):
        enabled_plugins = ':'.join(self.plugins.get_enabled_plugins())
        self.config.set('enabled_plugins', enabled_plugins)
        self.save_window_settings()
        self.config.save()
        self.plugins.shutdown_all_plugins()
        self.manager.quit()
        gtk.main_quit()


## For testing purposes, create a copy of the interface
if __name__ == "__main__":
    interface = DelugeGTK()
    interface.start()
