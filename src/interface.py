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

import os
import signal
import gobject
import pygtk
pygtk.require('2.0')
import gtk

import core
import common
import dialogs
import dgtk
import ipc_manager
import plugins
import tab_details

class DelugeGTK:
    def __init__(self):
        self.ipc_manager = ipc_manager.Manager(self)
        #Start the Deluge Manager:
        self.manager = core.Manager(common.CLIENT_CODE, common.CLIENT_VERSION, 
            '%s %s' % (common.PROGRAM_NAME, common.PROGRAM_VERSION), 
            common.CONFIG_DIR)
        self.plugins = plugins.PluginManager(self.manager, self)
        self.plugins.add_plugin_dir(common.PLUGIN_DIR)
        if os.path.isdir(os.path.join(common.CONFIG_DIR , 'plugins')):
            self.plugins.add_plugin_dir(os.path.join(common.CONFIG_DIR, 
                'plugins'))
        self.plugins.scan_for_plugins()
        self.config = self.manager.get_config()
        #Set up the interface:
        self.wtree = gtk.glade.XML(common.get_glade_file("delugegtk.glade"), 
            domain='deluge')
        self.window = self.wtree.get_widget("main_window")
        self.toolbar = self.wtree.get_widget("tb_left")
        self.window.drag_dest_set(gtk.DEST_DEFAULT_ALL, [('text/uri-list', 0, 
            80)], gtk.gdk.ACTION_COPY) 
        self.window.connect("delete_event", self.close)
        self.window.connect("key_press_event", self.key_pressed)
        self.window.connect("drag_data_received", self.on_drag_data)
        self.window.connect("window-state-event", self.window_state_event)
        self.window.connect("configure-event", self.window_configure_event)
        self.window.set_title(common.PROGRAM_NAME)
        if not common.windows_check():
            self.window.set_icon(common.get_logo(48))
        # self.notebook is used by plugins
        self.notebook = self.wtree.get_widget("torrent_info")
        self.notebook.connect("switch-page", self.notebook_switch_page)
        self.notebook.connect("page-reordered", self.notebook_page_reordered)
        self.notebook.connect("page-added", self.notebook_page_added)
        

        # Tabs
        self.tab_details = tab_details.DetailsTabManager(self.wtree,
                                                         self.manager)
        
        self.statusbar = self.wtree.get_widget("statusbar")
        
        self.build_tray_icon()
        self.has_tray = True
        
        self.build_torrent_table()
        self.load_status_icons()

        # Set the Torrent menu bar sub-menu to the same as the right-click 
        #Torrent pop-up menu
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

        def send_info():
            import time
            
            def _run_script():
                common.send_info(self.config.get("enabled_plugins"))
            
            info_file = os.path.join(common.CONFIG_DIR, 'infosent')
            
            # Check if we've done this within the last week
            if os.path.exists(info_file):
                if time.time() - os.stat(info_file)[8] >= 60 * 60 * 24 * 7:
                    _run_script()
            else:
                _run_script()        

        if self.config.get("send_info"):
            send_info()

        try:
            import gnome.ui
            self.client = gnome.ui.Client()
            self.client.connect("die", self.shutdown)
        except:
            pass

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        if not common.windows_check(): 
            signal.signal(signal.SIGHUP, self.shutdown)
        else:
            from win32api import SetConsoleCtrlHandler
            from win32con import CTRL_CLOSE_EVENT
            result = 0
            def win_handler(self, ctrl_type):
                if ctrl_type == CTRL_CLOSE_EVENT:
                    self.shutdown()
                    result = 1
                    return result
            SetConsoleCtrlHandler(win_handler)

        self.dht_timer = 0
        self.dht_skip = False
        for torrent in self.manager.get_queue():
            unique_ID = self.manager.get_torrent_unique_id(torrent)
            try:
                if self.manager.unique_IDs[unique_ID].uploaded_memory:
                    self.manager.unique_IDs[unique_ID].initial_uploaded_memory = \
                        self.manager.unique_IDs[unique_ID].uploaded_memory
                if self.manager.unique_IDs[unique_ID].trackers_changed:
                    self.manager.replace_trackers(unique_ID, \
                        self.manager.unique_IDs[unique_ID].trackers)
            except AttributeError:
                pass

    def connect_signals(self):
        self.wtree.signal_autoconnect({
                    ## File Menu
                    "add_torrent": self.add_torrent_clicked,
                    "add_torrent_url": self.add_torrent_url_clicked,
                    "remove_torrent": self.remove_torrent_clicked,
                    "menu_quit": self.quit,
                    ## Edit Menu
                    "select_all_torrents": self.select_all_torrents,
                    "plugin_clicked": self.show_plugin_dialog_clicked,
                    "pref_clicked": self.show_preferences_dialog_clicked,
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
                    "launch_homepage": self.launch_homepage,
                    "launch_community": self.launch_community,
                    "launch_faq": self.launch_faq,
                    "launch_donate": self.launch_donate,
                    "show_about_dialog": self.show_about_dialog,
                    "launchpad": self.launchpad,
                    "run_wizard": self.run_wizard,
                    ## Toolbar
                    "tor_start": self.tor_start,
                    "tor_pause": self.tor_pause,
                    "update_tracker": self.update_tracker,
                    "scrape_tracker": self.scrape_tracker,
                    "clear_finished": self.clear_finished,
                    "queue_up": self.q_torrent_up,
                    "queue_down": self.q_torrent_down
                    })
        
    def notebook_switch_page(self, notebook, page, page_num):
        # Force an update when user changes the notebook tab.
        # See notes in torrent_clicked() why we doing it this way. The only
        # difference here is that notebook_switch_page() is called by signal
        # 'switch-page' from GTK before notebook is switched to page_num, so
        # queue up update routines so they are called after page is actually
        # showed. See docs on 'switch-page' signal for gtk.Notebook.
        
        gobject.timeout_add(10, self.update_torrent_info_widget)
        gobject.timeout_add(10, self.plugins.update_active_plugins)
    
    def notebook_page_reordered(self, notebook, page, page_num):
        if page_num == 0:
            notebook.reorder_child(page, 1)
	
    def notebook_page_added(self, notebook, page, page_num):
        notebook.set_tab_reorderable(page, True)

    def pause_all_clicked(self, arg=None):
        self.manager.pause_all()

    def launch_browser_clicked(self, arg=None):
        try:
            import browser
            browser.Browser()
        except:
            dialogs.show_popup_warning(self.window, _("Unable to state browser.  \
Make sure you have python-gnome2-extras installed or try setting your LD_LIBRARY_PATH \
and MOZILLA_FIVE_HOME environment variables to /usr/lib/firefox"))

    def resume_all_clicked(self, arg=None):
        self.manager.resume_all()

    def key_pressed(self, widget, key):
        """captures keys"""
        if key.keyval == gtk.keysyms.Delete:
            self.remove_torrent_clicked()
        elif key.keyval in (gtk.keysyms.N, gtk.keysyms.n) and (key.state & \
            gtk.gdk.CONTROL_MASK) != 0:
            self.add_torrent_clicked()
        elif key.keyval in (gtk.keysyms.L, gtk.keysyms.l) and (key.state & \
            gtk.gdk.CONTROL_MASK) != 0:
            self.add_torrent_url_clicked()
        elif key.keyval in (gtk.keysyms.P, gtk.keysyms.p) and (key.state & \
            gtk.gdk.CONTROL_MASK) != 0:
            self.tor_pause(widget)
        elif key.keyval in (gtk.keysyms.R, gtk.keysyms.r) and (key.state & \
            gtk.gdk.CONTROL_MASK) != 0:
            self.tor_start(widget)

    def build_tray_icon(self):
        self.tray_icon = gtk.status_icon_new_from_icon_name('deluge')
        
        self.tray_glade = gtk.glade.XML(common.get_glade_file\
            ("tray_menu.glade"), domain='deluge')
        self.tray_menu  = self.tray_glade.get_widget("tray_menu")
        self.tray_glade.signal_autoconnect({
            "quit": self.quit,
            "pause_all": self.pause_all_clicked,
            "resume_all": self.resume_all_clicked,
            "add_torrent": self.add_torrent_clicked,
            "show_hide_window_toggled": self.show_hide_window_toggled
        })
        
        self.tray_glade.get_widget("download-limit-image").set_from_file(
            common.get_pixmap('downloading16.png'))
        self.tray_glade.get_widget("upload-limit-image").set_from_file(
            common.get_pixmap('seeding16.png'))
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
        self.tray_glade.get_widget("download_limit").set_submenu(
            self.submenu_bwdownset)
        self.tray_glade.get_widget("upload_limit").set_submenu(
            self.submenu_bwupset)
        
        # Show the sub-menus for all to see
        self.submenu_bwdownset.show_all()
        self.submenu_bwupset.show_all()

    def build_menu_radio_list(self, value_list, callback, pref_value=None, 
        suffix=None, show_notset=False, notset_label=None, notset_lessthan=0, 
        show_other=False, show_activated=False, activated_label=None):
        # Build a menu with radio menu items from a list and connect them to 
        # the callback. The pref_value is what you would like to test for the 
        # default active radio item.
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
                    menuitem = gtk.RadioMenuItem(group, str(value) + " " + \
                        suffix)
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
        str_bwdown = widget.get_children()[0].get_text().rstrip(" " + 
                        _("KiB/s"))
        if str_bwdown == _("Unlimited"):
            str_bwdown = -1
        
        if str_bwdown == _("Other..."):
            dialog_glade = gtk.glade.XML(common.get_glade_file(
                "dgtkpopups.glade"))
            speed_dialog = dialog_glade.get_widget("speed_dialog")
            spin_title = dialog_glade.get_widget("spin_title")
            spin_title.set_text(_("Download Speed (KiB/s):"))
            spin_speed = dialog_glade.get_widget("spin_speed")
            speed_dialog.set_transient_for(self.window)
            speed_dialog.set_modal(True)
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
        str_bwup = widget.get_children()[0].get_text().rstrip(" " + 
            _("KiB/s"))
        if str_bwup == _("Unlimited"):
            str_bwup = -1
        
        if str_bwup == _("Other..."):
            dialog_glade = gtk.glade.XML(common.get_glade_file(
                "dgtkpopups.glade"))
            speed_dialog = dialog_glade.get_widget("speed_dialog")
            spin_title = dialog_glade.get_widget("spin_title")
            spin_title.set_text(_("Upload Speed (KiB/s):"))
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

    # Use is_showing_dlg argument as a kind of static variable to not add
    # unlock tray dialog state to instance where it will be not used except as
    # in this method. Assigning list to is_showing_dlg is intentional.
    def unlock_tray(self, comingnext, is_showing_dlg=[False]):
        if is_showing_dlg[0]:
            return
        
        is_showing_dlg[0] = True
        
        entered_pass = gtk.Entry(25)
        entered_pass.set_activates_default(True)
        entered_pass.set_width_chars(25)
        entered_pass.set_visibility(False)
        entered_pass.show()
        tray_lock = gtk.Dialog(title=_("Deluge is locked"), parent=self.window,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, 
            gtk.RESPONSE_ACCEPT))
        label = gtk.Label(_("Deluge is password protected.\nTo show the Deluge \
window, please enter your password"))
        label.set_line_wrap(True)
        label.set_justify(gtk.JUSTIFY_CENTER)
        tray_lock.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        tray_lock.set_size_request(400, 200)
        tray_lock.set_default_response(gtk.RESPONSE_ACCEPT)
        tray_lock.vbox.pack_start(label)
        tray_lock.vbox.pack_start(entered_pass)
        tray_lock.show_all()
        if tray_lock.run() == gtk.RESPONSE_ACCEPT:
            import sha
            #for backward compatibility
            if len(self.config.get("tray_passwd")) != 40:
                password = sha.new(self.config.get("tray_passwd")).hexdigest()
            else:
                password = self.config.get("tray_passwd")
            if password == sha.new(entered_pass.get_text()).hexdigest():
                if comingnext == "mainwinshow":
                    self.window.show()
                elif comingnext == "prefwinshow":
                    self.show_preferences_dialog()
                elif comingnext == "plugwinshow":
                    self.show_plugin_dialog()
                elif comingnext == "quitus":
                    self.shutdown()

        tray_lock.destroy()
        
        is_showing_dlg[0] = False
        
        return True

    def load_status_icons(self):
        self.status_icons = \
            {'paused': gtk.gdk.pixbuf_new_from_file(
                           common.get_pixmap("inactive16.png")),
             'seeding': gtk.gdk.pixbuf_new_from_file(
                         common.get_pixmap("seeding16.png")),
             'downloading' : gtk.gdk.pixbuf_new_from_file(
                                 common.get_pixmap("downloading16.png"))}
    
    def list_of_trackers(self, obj=None):
        torrent = self.get_selected_torrent()
        if torrent is not None:
            trackerslist = self.manager.get_trackers(torrent)
            self.show_edit_tracker_dialog(trackerslist)

    def cancel_edit_window(self, arg=None):
        self.edit_window.destroy()

    def accept_edit_window(self, arg=None):
        torrent = self.get_selected_torrent()
        self.textlist = self.textbuffer.get_text(self.textbuffer.\
            get_start_iter(), self.textbuffer.get_end_iter(), 
            include_hidden_chars=False).strip()
        self.manager.replace_trackers(torrent, self.textlist)
        self.edit_window.destroy()

    def show_edit_tracker_dialog(self, list):
        self.textbuffer = gtk.TextBuffer(table=None)
        self.textbuffer.set_text(list)
        self.edit_glade = gtk.glade.XML(common.get_glade_file(
            "edit_trackers.glade"))
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
                # Force UI update as we don't update it while minimized
                self.update()
                self.window.present()
        else:
            if self.config.get("lock_tray"):
                self.unlock_tray("mainwinshow")
            else:
                self.load_window_geometry()
                self.window.show()
                # Force UI update as we don't update it while in tray
                self.update()
    
    def show_hide_window_toggled(self, widget):
        if widget.get_active() and not self.window.get_property("visible"):
            if self.config.get("lock_tray"):
                self.unlock_tray("mainwinshow")
            else:
                self.window.show()
        elif not widget.get_active() and self.window.get_property("visible"):
            self.window.hide()

    def build_torrent_table(self):
        ## Create the torrent listview
        self.torrent_view = self.wtree.get_widget("torrent_view")
        torrent_glade = gtk.glade.XML(common.get_glade_file(
            "torrent_menu.glade"), domain='deluge')
        torrent_glade.signal_autoconnect({
                        "remove_torrent": self.remove_torrent_clicked,
                        "edit_trackers": self.list_of_trackers,
                        "tor_start": self.tor_start,
                        "torrent_switch_recheck": self.torrent_switch_recheck,
                        "tor_pause": self.tor_pause,
                        "update_tracker": self.update_tracker,
                        "clear_finished": self.clear_finished,
                        "open_folder_clicked": self.open_folder,
                        "queue_up": self.q_torrent_up,
                        "queue_down": self.q_torrent_down,
                        "queue_bottom": self.q_to_bottom,
                        "queue_top": self.q_to_top
                                                })
        self.torrent_menu = torrent_glade.get_widget("torrent_menu")
        # unique_ID, Q#, Status Icon, Name, Size, Progress, Message, Seeders, 
        # Peers, DL, UL, ETA, Share
        self.torrent_model = gtk.ListStore(int, gobject.TYPE_UINT, 
            gtk.gdk.Pixbuf, str, gobject.TYPE_UINT64, float, str, int, int, 
            int, int, int, int, gobject.TYPE_UINT64, float, float)
        # Stores unique_ID -> gtk.TreeRowReference's mapping for quick look up
        self.torrent_model_dict = {}

        self.torrent_view.connect("row-activated", self.double_click_folder)
        self.torrent_view.set_model(self.torrent_model)
        self.torrent_view.set_rules_hint(True)
        self.torrent_view.set_reorderable(True)
        self.torrent_view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        def peer(column, cell, model, iter, data):
            c1, c2 = data
            a = model.get_value(iter, c1)
            b = model.get_value(iter, c2)
            cell.set_property('text', '%d (%d)'%(a, b))
        
        def time(column, cell, model, iter, data):
            time = model.get_value(iter, data)
            if time < 0 or time == 0:
                time_str = _("Infinity")
            else:
                time_str = common.ftime(time)
            cell.set_property('text', time_str)
            
        def availability(column, cell, model, iter, data):
            availability_str = model.get_value(iter, data)
            cell.set_property('text', "%.3f" % availability_str)
            
        def ratio(column, cell, model, iter, data):
            ratio = model.get_value(iter, data)
            if ratio == -1:
                ratio_str = _("Unknown")
            else:
                ratio_str = "%.3f" % ratio
            cell.set_property('text', ratio_str)
        
        ## Initializes the columns for the torrent_view
        (TORRENT_VIEW_COL_UID, TORRENT_VIEW_COL_QUEUE, 
        TORRENT_VIEW_COL_STATUSICON, TORRENT_VIEW_COL_NAME,
        TORRENT_VIEW_COL_SIZE, TORRENT_VIEW_COL_PROGRESS, 
        TORRENT_VIEW_COL_STATUS, TORRENT_VIEW_COL_CONNECTED_SEEDS, 
        TORRENT_VIEW_COL_SEEDS, TORRENT_VIEW_COL_CONNECTED_PEERS, 
        TORRENT_VIEW_COL_PEERS, TORRENT_VIEW_COL_DOWNLOAD, 
        TORRENT_VIEW_COL_UPLOAD, TORRENT_VIEW_COL_ETA, 
        TORRENT_VIEW_COL_AVAILABILITY, TORRENT_VIEW_COL_RATIO) = range(16)

        self.queue_column = dgtk.add_text_column(self.torrent_view, "#", 
            TORRENT_VIEW_COL_QUEUE, width=self.config.get("queue_width"))
        self.name_column = dgtk.add_texticon_column(self.torrent_view, _("Name"\
            ), TORRENT_VIEW_COL_STATUSICON, TORRENT_VIEW_COL_NAME, width=\
            self.config.get("name_width"))
        self.size_column = dgtk.add_func_column(self.torrent_view, _("Size"), \
            dgtk.cell_data_size, TORRENT_VIEW_COL_SIZE, width=self.config.get\
            ("size_width"))
        self.status_column = dgtk.add_progress_column(self.torrent_view, _(\
            "Status"), TORRENT_VIEW_COL_PROGRESS, TORRENT_VIEW_COL_STATUS, 
            width=self.config.get("status_width"))
        self.seed_column = dgtk.add_func_column(self.torrent_view, _("Seeders")\
            , peer, (TORRENT_VIEW_COL_CONNECTED_SEEDS, TORRENT_VIEW_COL_SEEDS)\
            , width=self.config.get("seed_width"))
        self.peer_column = dgtk.add_func_column(self.torrent_view, _("Peers"), \
            peer, (TORRENT_VIEW_COL_CONNECTED_PEERS, TORRENT_VIEW_COL_PEERS), \
            width=self.config.get("peer_width"))
        self.dl_column = dgtk.add_func_column(self.torrent_view, _("Down Speed"\
            ), dgtk.cell_data_speed, TORRENT_VIEW_COL_DOWNLOAD, width=\
            self.config.get("dl_width"))
        self.ul_column = dgtk.add_func_column(self.torrent_view, _("Up Speed"), 
            dgtk.cell_data_speed, TORRENT_VIEW_COL_UPLOAD, width=\
            self.config.get("ul_width"))
        self.eta_column = dgtk.add_func_column(self.torrent_view, _("ETA"), 
            time, TORRENT_VIEW_COL_ETA, width=self.config.get("eta_width"))
        self.availability_column = dgtk.add_func_column(self.torrent_view, 
            _("Avail."), availability, TORRENT_VIEW_COL_AVAILABILITY, width=\
            self.config.get("availability_width"))
        self.share_column = dgtk.add_func_column(self.torrent_view, _("Ratio"), 
            ratio, TORRENT_VIEW_COL_RATIO, width=self.config.get("share_width"))
        
        self.name_column.set_sort_column_id(TORRENT_VIEW_COL_NAME)
        self.seed_column.set_sort_column_id(TORRENT_VIEW_COL_CONNECTED_SEEDS)
        self.peer_column.set_sort_column_id(TORRENT_VIEW_COL_CONNECTED_PEERS)
        
        self.torrent_model.set_sort_column_id(TORRENT_VIEW_COL_QUEUE, 
                                              gtk.SORT_ASCENDING)
        try:
            self.torrent_view.get_selection().set_select_function(
                self.torrent_clicked, full=True)
        except TypeError:
            self.torrent_view.get_selection().set_select_function(
                self.old_t_click)
        self.torrent_view.connect("button-press-event", 
            self.torrent_view_clicked)

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
        return self.torrent_clicked(self.torrent_view.get_selection(), 
            self.torrent_model, path, False)
        
    def torrent_clicked(self, selection, model, path, is_selected):
        if is_selected:
            # Torrent is already selected, we don't need to do anything
            return True
        
        # We don't call update function directly, because torrent_clicked()
        # called by GTK when torrent is not selected yet(read docs on 
        # gtk.TreeSelection.set_select_function()), but update routines
        # expect already selected torrent. So queue update functions until we
        # exit from torrent_clicked() and torrent will be actually selected by
        # the time update functions called. Hope 10ms will be always enough
        # for this.
        gobject.timeout_add(10, self.update_torrent_info_widget)
        gobject.timeout_add(10, self.plugins.update_active_plugins)

        return True
    
    def torrent_view_clicked(self, widget, event):
        if event.button == 3:
            data = self.torrent_view.get_path_at_pos(int(event.x), int(event.y))
            if data is None:
                return True
            
            path = data[0]
            is_selected = self.torrent_view.get_selection().path_is_selected\
                (path)
            if not is_selected:
                self.torrent_view.grab_focus()
                self.torrent_view.set_cursor(path)
                
            self.torrent_menu.popup(None, None, None, event.button, 
                                    event.time)
            
            return is_selected
        else:
            return False

    def double_click_folder(self, tree, path, view_column):
        self.open_folder(view_column)

    def open_folder(self, widget, uids=None):
        if not common.windows_check():
            if self.config.get("open_folder_stock"):
                if self.config.get("file_manager") == common.FileManager.xdg:
                    file_manager = "xdg-open"
                elif self.config.get("file_manager") == common.FileManager.\
                    konqueror:
                    file_manager = "konqueror"
                elif self.config.get("file_manager") == common.FileManager.nautilus:
                    file_manager = "nautilus"
                elif self.config.get("file_manager") == common.FileManager.thunar:
                    file_manager = "thunar"
            else:
                file_manager = self.config.get("open_folder_location")
        else:
            file_manager = "explorer.exe"

        if not uids:
            unique_ids = self.get_selected_torrent_rows()
        else:
            unique_ids = uids

        try:
            for uid in unique_ids:
                torrent_path = self.manager.get_torrent_path(uid)
                common.exec_command(file_manager, torrent_path)
        except KeyError:
            pass

    def torrent_switch_recheck(self, widget=None, switch=False):
        unique_ids = self.get_selected_torrent_rows()
        for uid in unique_ids:
            torrent_state = self.manager.get_torrent_state(uid)
            order = torrent_state['queue_pos']
            path = self.manager.unique_IDs[uid].filename
            if not switch:
                save_dir = self.manager.unique_IDs[uid].save_dir
                delete_old = False
            else:
                save_dir = dialogs.show_directory_chooser_dialog(self.window, \
                _("Choose a directory to switch torrent source to" + " - %s" % \
                    self.manager.get_torrent_state(uid)['name']))
                if save_dir:
                    delete_old = dialogs.show_popup_question(self.window, \
                        _("Delete the old torrent source?"))
                else:
                    delete_old = False
            if save_dir:
                trackerslist = self.manager.unique_IDs[uid].trackers
                try:
                    trackers_changed = self.manager.unique_IDs[uid].trackers_changed
                except AttributeError:
                     trackers_changed = 0
                self.manager.pickle_state()
                uploaded_memory = self.manager.unique_IDs[uid].uploaded_memory
                priorities = self.manager.get_priorities(uid)
                save_info = [path, save_dir, order, trackerslist, \
                                uploaded_memory, priorities, trackers_changed, \
                            delete_old]
                try:
                    os.remove(self.manager.unique_IDs[uid].filename + ".fastresume")
                except:
                    pass
                if save_info[7]:
                    self.manager.remove_torrent(uid, True, False)
                else:
                    self.manager.remove_torrent(uid, False, False)
                self.torrent_model_remove(uid)
                self.update()
                unique_ID = self.manager.add_torrent(save_info[0], save_info[1], \
                    self.config.get("use_compact_storage"))
                self.torrent_model_append(unique_ID)
                self.update()
                self.manager.prioritize_files(unique_ID, save_info[5], update_files_removed=False)
                if save_info[4]:
                    self.manager.unique_IDs[unique_ID].initial_uploaded_memory = \
                        save_info[4]
                    self.manager.pickle_state()
                if save_info[6]:
                    try:
                        self.manager.replace_trackers(unique_ID, save_info[3])
                    except:
                       pass
                torrent_state = self.manager.get_torrent_state(unique_ID)
                current_order = torrent_state['queue_pos']
                if current_order > save_info[2]:
                    diff = current_order - save_info[2]
                    for x in range(diff):
                        self.manager.queue_up(unique_ID)
                    self.update()
                else:
                    diff = save_info[2] - current_order
                    for x in range(diff):
                        self.manager.queue_down(unique_ID)
                    self.update()
    
    def tor_start(self, widget):
        unique_ids = self.get_selected_torrent_rows()
        try:
            for uid in unique_ids:
                torrent_state = self.manager.get_torrent_state(uid)
                if torrent_state["is_paused"]:
                    self.manager.set_user_pause(uid, False, True)
            
            self.update()

        except KeyError:
            pass

    def tor_pause(self, widget):
        try:
            unique_ids = self.get_selected_torrent_rows()
            for uid in unique_ids:
                self.manager.set_user_pause(uid, True, True)
                torrent_state = self.manager.get_torrent_state(uid)
            self.update()
        except:
            pass

    def show_about_dialog(self, arg=None):
        dialogs.show_about_dialog(self.window)

    def run_wizard(self, arg=None):
        import wizard
        wizard.WizardGTK()
        #reload config file
        import pref
        self.config = pref.Preferences(os.path.join(common.CONFIG_DIR, "prefs.state"))
        self.apply_prefs()

    def show_preferences_dialog(self):
        active_port = self.manager.get_state()['port']
        preferences_dialog = dialogs.PreferencesDlg(self.config, active_port, 
            self.plugins)
        preferences_dialog.show(self, self.window)

    def show_preferences_dialog_clicked(self, arg=None):
        if self.config.get("enable_system_tray") and \
            self.config.get("lock_tray") and not self.window.get_property(
                "visible"):
            self.unlock_tray("prefwinshow")
        else:
            self.show_preferences_dialog()

    def show_plugin_dialog(self, plugin_tab=True):
        active_port = self.manager.get_state()['port']
        plugin_dialog = dialogs.PreferencesDlg(self.config, active_port, \
            self.plugins, plugin_tab=True)
        plugin_dialog.show(self, self.window)

    def show_plugin_dialog_clicked(self, arg=None):
        if self.config.get("enable_system_tray") and self.config.get(
            "lock_tray") and not self.window.get_property("visible"):
            self.unlock_tray("plugwinshow")
        else:
            self.show_plugin_dialog(plugin_tab=True)

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
        if self.config.get("max_download_speed") not in self.config.get(
            "tray_downloadspeedlist") and self.config.get("max_download_speed")\
                 >= 0:
            # We prepend this value and remove the last value in the list
            self.config.get("tray_downloadspeedlist").insert(0, self.config.get(
                "max_download_speed"))
            self.config.get("tray_downloadspeedlist").pop()

        # Do the same for the upload speed limits
        if self.config.get("max_upload_speed") not in self.config.get(
            "tray_uploadspeedlist") and self.config.get("max_upload_speed") >= \
                0:
            # We prepend this value and remove the last value in the list
            self.config.get("tray_uploadspeedlist").insert(0, self.config.get(
                "max_upload_speed"))
            self.config.get("tray_uploadspeedlist").pop()

        # Re-build the tray sub-menu to display the correct active radio item
        self.build_tray_bwsetsubmenu()
        
        # Apply the preferences in the core
        self.manager.apply_prefs()
        self.manager.pe_settings(self.config.get("encout_state"), 
            self.config.get("encin_state"), self.config.get("enclevel_type"), 
                self.config.get("pref_rc4"))
        if self.config.get("peer_proxy"):
            self.manager.proxy_settings(self.config.get("peer_proxy_hostname"), 
                self.config.get("peer_proxy_username"), self.config.get(
                    "peer_proxy_password"), 
                    int(self.config.get("peer_proxy_port")), self.config.get(
                        "peer_proxy_type"), "peer")
        if self.config.get("dht_proxy"):
            self.manager.proxy_settings(self.config.get("dht_proxy_hostname"), 
                self.config.get("dht_proxy_username"), self.config.get(
                    "dht_proxy_password"), 
                    int(self.config.get("dht_proxy_port")), self.config.get(
                        "dht_proxy_type"), "dht")
        if self.config.get("tracker_proxy"):
            self.manager.proxy_settings(self.config.get(
                "tracker_proxy_hostname"), 
                self.config.get("tracker_proxy_username"), self.config.get(
                    "tracker_proxy_password"), 
                    int(self.config.get("tracker_proxy_port")), self.config.get(
                        "tracker_proxy_type"), "tracker")
        if self.config.get("web_proxy"):
            self.manager.proxy_settings(self.config.get("web_proxy_hostname"), 
                self.config.get("web_proxy_username"), self.config.get(
                    "web_proxy_password"), 
                    int(self.config.get("web_proxy_port")), self.config.get(
                        "web_proxy_type"), "web")

    def get_message_from_state(self, unique_id, torrent_state):
        state = torrent_state['state']
        is_paused = torrent_state['is_paused']
        progress = torrent_state['progress']
        progress = '%d%%' % (progress * 100)
        if is_paused:
            if self.manager.is_user_paused(unique_id):
                message = _("Paused %s") % progress
            else:
                message = _("Queued %s") % progress
        else:
            try:
                message = core.STATE_MESSAGES[state]
                if state in (1, 3, 4, 7):
                    message = '%s %s' % (message, progress)
            except IndexError:
                message = ''
        return message
    
    # UID, Q#, Name, Size, Progress, Message, Seeders, Peers, DL, UL, ETA, 
    # Share
    def get_torrent_state_list(self, unique_id, state):
        queue = state['queue_pos']
        name = state['name']
        size = state['total_wanted']
        progress = state['progress'] * 100
        message = self.get_message_from_state(unique_id, state)
        availability = state['distributed_copies']
        share = self.manager.calc_ratio(unique_id, state)

        # setting after initial paused state ensures first change gets updated
        if state["is_paused"]:
            # Update stats to pause state immediately so interface does not
            # need to keep updating when paused
            seeds = seeds_t = peers = peers_t = dl_speed = ul_speed = eta = 0
            # Set status icon as pause
            status_icon = self.status_icons['paused']
        else:
            seeds = state['num_seeds']
            seeds_t = state['total_seeds']
            peers = state['num_peers']
            peers_t = state['total_peers']
            dl_speed = int(state['download_rate'])
            ul_speed = int(state['upload_rate'])
            try:
                eta = common.get_eta(size, state["total_wanted_done"], 
                                     dl_speed)
            except ZeroDivisionError:
                eta = 0
            # Set the appropriate status icon
            if state["is_seed"] or \
               state["state"] == self.manager.constants["STATE_FINISHED"]:
                status_icon = self.status_icons['seeding']
            else:
                status_icon = self.status_icons['downloading']
    
        rlist =  [unique_id, queue, status_icon, name, size, progress, 
                  message, seeds, seeds_t, peers, peers_t, dl_speed, ul_speed, 
                  eta, availability, share]

        return rlist
    
    ## Start the timer that updates the interface
    def start(self, cmd_line_torrents=None):
        if cmd_line_torrents is None:
            cmd_line_torrents = []
        
        if not(self.config.get("start_in_tray") and \
               self.config.get("enable_system_tray") and 
               self.has_tray) and not self.window.get_property("visible"):
            print "Showing window"
            self.window.show()
        
        ## add torrents in manager's queue to interface
        for torrent in self.manager.get_queue():
            unique_id = self.manager.get_torrent_unique_id(torrent)
            self.torrent_model_append(unique_id)
            
        for torrent_file in cmd_line_torrents:
            self.interactive_add_torrent(torrent_file)
             
        # Call update now so everything is up-to-date when the window gains 
        # focus on startup
        self.update()
        gobject.timeout_add(int(1000*self.manager.config.get("gui_update_interval")), self.update)
        gobject.timeout_add(250000, self.manager.pickle_state)
        gobject.timeout_add(300000, self.manager.save_fastresume_data)

        # Load plugins after we showed main window (if not started in tray)
        self.load_plugins()
        self.load_tabs_order()
        if self.config.get("new_releases"):
            self.new_release_check()

        try:
            gobject.threads_init()
            gtk.gdk.threads_enter()
            gtk.main()
            gtk.gdk.threads_leave()
        except KeyboardInterrupt:
            self.shutdown()

    def new_release_check(self):
        import socket
        import urllib
        timeout = 5
        socket.setdefaulttimeout(timeout)
        try:
            gtk.gdk.threads_enter()
        except:
            pass
        try:
            new_release = urllib.urlopen("http://download.deluge-torrent.org/version").read().strip()
        except IOError:
            print "Network error while trying to check for a newer version of \
Deluge"
            try:
                gtk.gdk.threads_leave()
            except:
                pass
            return

        if new_release > common.PROGRAM_VERSION:
            result = dialogs.show_popup_question(None, _("There is a newer version \
of Deluge.  Would you like to be taken to our download site?"))
            if result:
                common.open_url_in_browser('http://download.deluge-torrent.org/')
            else:
                pass
        try:
            gtk.gdk.threads_leave()
        except:
            pass

    def load_plugins(self):
        enable_plugins = self.config.get('enabled_plugins').split(':')
        for plugin in enable_plugins:
            if plugin != "Blocklist Importer" and plugin != "Torrent Pieces" and plugin != "FlexRSS":
                try:
                    self.plugins.enable_plugin(plugin)
                except KeyError:
                    pass
        if "Blocklist Importer" in enable_plugins:
            self.plugins.enable_plugin("Blocklist Importer")
        if "FlexRSS" in enable_plugins:
            self.plugins.enable_plugin("FlexRSS")

    ## Call via a timer to update the interface
    def update(self):
        if self.config.get("autoload") and self.config.get("default_autoload_path"):
            for filename in os.listdir(self.config.get("default_autoload_path")):
                if filename[-len(".torrent"):].lower() == ".torrent":
                    try:
                        self.interactive_add_torrent_path(os.path.join(\
                        self.config.get("default_autoload_path"), filename), \
                        self.config.get("default_download_path"))
                        os.remove(os.path.join(self.config.get("default_autoload_path"), filename))
                    except:
                        pass
        # Handle the events
        self.manager.handle_events()

        # We need to apply the queue changes
        self.manager.apply_queue()
        
        self.update_interface = self.window.get_property("visible") and not \
            self.is_minimized
        
        # Make sure that the interface still exists
        try:
            self.wtree.get_widget("torrent_info").get_current_page()
        except AttributeError:
            return False
        
        # Update Statusbar and Tray Tips
        self.update_statusbar_and_tray()

        #Update any active plugins
        self.plugins.update_active_plugins()

        #Plugins have updated info, so clear it
        self.manager.clear_update_files_removed()
        
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
            self.wtree.get_widget("toolbutton_clear").set_sensitive(itr is not None)
            self.wtree.get_widget("toolbutton_remove").set_sensitive(itr is \
                not None)
            self.wtree.get_widget("toolbutton_resume").set_sensitive(itr is \
                not None)
            self.wtree.get_widget("toolbutton_pause").set_sensitive(itr is \
                not None)
            if len(self.manager.get_queue()) > 1:
                self.wtree.get_widget("toolbutton_up").set_sensitive(True)
                self.wtree.get_widget("toolbutton_down").set_sensitive(True)
            else:
                self.wtree.get_widget("toolbutton_up").set_sensitive(False)
                self.wtree.get_widget("toolbutton_down").set_sensitive(False)
        
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
                    # queue pos, selected files size and status message.
                    # All the other columns are unchanged.
                    message = self.get_message_from_state(unique_id, state)
                    dgtk.update_store(self.torrent_model, itr, (1, 4, 6), 
                                      (state['queue_pos'], 
                                       state['total_wanted'],
                                       message))
                else:
                    tlist = self.get_torrent_state_list(unique_id, state)
                    dgtk.update_store(self.torrent_model, itr, 
                                      xrange(len(tlist)), tlist)
                        
                itr = self.torrent_model.iter_next(itr)
            torrent_selection = self.torrent_view.get_selection()
            selection_count = torrent_selection.count_selected_rows()
            
            # If no torrent is selected, select the first torrent:
            if selection_count == 0:
                torrent_selection.select_path("0")
                selection_count = 1
            
            if selection_count == 1:
                self.update_torrent_info_widget()
            else: # selection_count > 1
                self.clear_details_pane()
                
        return True
            
    def update_statusbar_and_tray(self):
        plugin_messages = self.plugins.get_plugin_tray_messages()
        core_state = self.manager.get_state()
        connections = core_state['num_connections']
        if self.config.get("max_connections_global") < 0 :
            max_connections = _("Unlimited")
        else:
            max_connections = self.config.get("max_connections_global")
        dlspeed = common.fspeed(core_state['download_rate'])
        ulspeed = common.fspeed(core_state['upload_rate'])

        if self.config.get("max_download_speed") < 0:
            dlspeed_max = _("Unlimited")
        else:
            dlspeed_max = common.fspeed(self.config.get(
                "max_download_speed_bps"))
        if self.config.get("max_upload_speed") < 0:
            ulspeed_max = _("Unlimited")
        else:
            ulspeed_max = common.fspeed(self.config.get("max_upload_speed_bps"))
        
        # Use self.statusbar_temp_msg instance var to allow plugins access it
        self.statusbar_temp_msg = '%s: %s (%s)  %s: %s (%s)  %s: %s (%s)' % (
            _("Connections"), connections, max_connections, _("Down Speed"), 
            dlspeed, dlspeed_max, _("Up Speed"), ulspeed, ulspeed_max)
        
        if 'DHT_nodes' in core_state:
            dht_peers = core_state['DHT_nodes']
            if dht_peers == -1:
                dht_peers = '?'
            if dht_peers == 0:
                self.dht_timer += 1
                if (self.dht_timer == 20) and (self.manager.\
                    get_state()['num_peers'] > 0) and (not self.dht_skip):
                    self.manager.set_DHT(False)
                    os.remove(common.CONFIG_DIR + '/dht.state')
                    self.manager.set_DHT(True)
                    self.dht_skip = True
            else:
                dht_peers = str(dht_peers)
            self.statusbar_temp_msg = self.statusbar_temp_msg + \
                                      '   [' + _("DHT") + ': %s]'%(dht_peers)
        # windows cant display more than 64 characters in systray tooltip
        if common.windows_check():
            #msg = _("Deluge Bittorrent Client")
            if ulspeed_max == _("Unlimited"):
                ulspeed_max = "*"
            if dlspeed_max == _("Unlimited"):
                dlspeed_max = "*" 
            msg = '%s\n%s: %s (%s)\n%s: %s (%s)' % (\
            _("Deluge"), _("Download"), dlspeed, \
            dlspeed_max, _("Upload"), ulspeed, ulspeed_max)
        else:
            msg = '%s\n%s: %s (%s)\n%s: %s (%s)%s' % (\
            _("Deluge Bittorrent Client"), _("Down Speed"), dlspeed, \
            dlspeed_max, _("Up Speed"), ulspeed, ulspeed_max, plugin_messages)
        
        self.tray_icon.set_tooltip(msg)

    def update_torrent_info_widget(self):
        unique_id = self.get_selected_torrent()
        # If no torrents added
        if unique_id is None:
            return
        
        page_num = self.wtree.get_widget("torrent_info").get_current_page()
        
        if page_num == 0: # Details
            self.tab_details.update(unique_id)
    
        # We have to return False here to stop calling this function by timer
        # over and over again, from self.torrent_clicked() for example.
        return False
    
    # Return the id of the last single selected torrent
    def get_selected_torrent(self):
        try:
            if self.torrent_view.get_selection().count_selected_rows() == 1:
                selected_path = self.torrent_view.get_selection().\
                                    get_selected_rows()[1][0]
                selected_torrent = self.torrent_model.get_value(
                    self.torrent_model.get_iter(selected_path), 0)
                return selected_torrent
        except (TypeError, ValueError):
            pass
        
        return None
            
    # Return a list of ids of the selected torrents
    def get_selected_torrent_rows(self):
        selected_ids = []
        selected_paths = self.torrent_view.get_selection().get_selected_rows()\
            [1]
        
        try:
            for path in selected_paths:
                selected_ids.append(self.torrent_model.get_value(
                    self.torrent_model.get_iter(path), 0))
            return selected_ids
        except ValueError:
            return None
    
    def on_drag_data(self, widget, drag_context, x, y, selection_data, info, 
        timestamp):
        import urllib
    
        uri_split = selection_data.data.strip().split()
        for uri in uri_split:
            if uri.startswith('file://') and common.windows_check():
                uri = uri[7:]
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
                return self.interactive_add_torrent(filename)

    def interactive_add_torrent(self, torrent):
        if self.config.get('use_default_dir'):
            path = self.config.get('default_download_path')
        else:
            path = dialogs.show_directory_chooser_dialog(self.window, 
                       _("Choose a download directory"))
            if path is None:
                return

        return self.interactive_add_torrent_path(torrent, path)

    def interactive_add_torrent_path(self, torrent, path):
        unique_id = False

        try:
            dumped_torrent = self.manager.dump_torrent_file_info(torrent)
            if self.config.get('enable_files_dialog') and not \
                self.config.get('enable_multi_only'):
                files_dialog = dialogs.FilesDlg(dumped_torrent)
                if files_dialog.show(self.window) == 1:
                    unique_id = self.manager.add_torrent(torrent, path, 
                                    self.config.get('use_compact_storage'), \
                                    self.config.get('start_paused'))
                    self.manager.prioritize_files(unique_id, 
                        files_dialog.get_priorities())
                    if files_dialog.is_private_flag_checked():
                        self.manager.set_priv(unique_id, True)
                else:
                    return False
            elif self.config.get('enable_files_dialog') and \
                self.config.get('enable_multi_only') and (len(dumped_torrent) > 1):
                files_dialog = dialogs.FilesDlg(dumped_torrent)
                if files_dialog.show(self.window) == 1:
                    unique_id = self.manager.add_torrent(torrent, path, 
                                    self.config.get('use_compact_storage'), \
                                    self.config.get('start_paused'))
                    self.manager.prioritize_files(unique_id, 
                        files_dialog.get_priorities())
                    if files_dialog.is_private_flag_checked():
                        self.manager.set_priv(unique_id, True)
                else:
                    return False
            elif self.config.get('enable_files_dialog') and \
                self.config.get('enable_multi_only') and not (len(dumped_torrent) > 1):
                unique_id = self.manager.add_torrent(torrent, path, 
                                self.config.get('use_compact_storage'), \
                                self.config.get('start_paused'))

            elif not self.config.get('enable_files_dialog'):
                unique_id = self.manager.add_torrent(torrent, path, 
                                self.config.get('use_compact_storage'), \
                                self.config.get('start_paused'))
        except core.InvalidEncodingError, e:
            print "InvalidEncodingError", e
            dialogs.show_popup_warning(self.window, _("An error occured while \
trying to add the torrent. It's possible your .torrent file is corrupted."))
        except core.DuplicateTorrentError, e:
            for unique_id in self.manager.unique_IDs:
                is_duplicate = self.manager.test_duplicate(torrent, unique_id)
                if is_duplicate:
                    break
            if is_duplicate:
                merge_dialog = dialogs.MergeDlg()
                if merge_dialog.show(self.window) == 1:
                    new_trackers_as_list = self.manager.dump_trackers(torrent)\
                        .splitlines()
                    original_trackers_as_list = self.manager.get_trackers(
                        unique_id).splitlines()
                    merged_trackers = []
                    for s in original_trackers_as_list, new_trackers_as_list:
                        for x in s:
                            merged_trackers.append(x)
                    #remove duplicates
                    d = {}
                    for k in merged_trackers:
                       d[k] = 1
                    merged_trackers_as_string = ''
                    for x in d.keys():
                        merged_trackers_as_string = merged_trackers_as_string + x + '\n'
                    self.manager.replace_trackers(unique_id, 
                        merged_trackers_as_string.strip())
            else:
                dialogs.show_popup_warning(self.window, _("Unknown duplicate \
torrent error."))
        except core.InsufficientFreeSpaceError, e:
            nice_need = common.fsize(e.needed_space)
            nice_free = common.fsize(e.free_space)
            dialogs.show_popup_warning(self.window, _("There is not enough free\
disk space to complete your download.") + "\n" + _("Space Needed:") + " " + \
nice_need + "\n" + _("Available Space:") + " " + nice_free)
        except core.InvalidEncodingError, e:
            print "invalid encoding\n"
        except Exception, e:
            print "Unable to add torrent:", e
        else:
            self.torrent_model_append(unique_id)

        return unique_id
            
    def launchpad(self, obj=None):
        common.open_url_in_browser('https://translations.launchpad.net/deluge/\
trunk/+pots/deluge')

    def launch_faq(self, obj=None):
        common.open_url_in_browser('http://deluge-torrent.org/faq.php')

    def launch_donate(self, obj=None):
        common.open_url_in_browser('http://deluge-torrent.org/downloads.php')

    def launch_community(self, obj=None):
        common.open_url_in_browser('http://forum.deluge-torrent.org/')

    def launch_homepage(self, obj=None):
        common.open_url_in_browser('http://deluge-torrent.org/')
            
    def add_torrent_clicked(self, obj=None):
        torrent = dialogs.show_file_open_dialog(self.window)
        if torrent is not None:
            for single in torrent:
                self.interactive_add_torrent(single)

    def add_torrent_url_clicked(self, obj=None):
        dlg = gtk.Dialog(_("Add torrent from URL"), self.window, 0,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OK, gtk.RESPONSE_OK))
        dlg.set_default_response(gtk.RESPONSE_OK)
        dlg.set_icon(common.get_logo(18))
        label = gtk.Label(_("Enter the URL of the .torrent to download"))
        entry = gtk.Entry()
        entry.connect("activate", lambda w : dlg.response(gtk.RESPONSE_OK))
        dlg.vbox.pack_start(label)
        dlg.vbox.pack_start(entry)
        if common.windows_check():
            import win32clipboard as clip 
            import win32con
            clip.OpenClipboard() 
            text=clip.GetClipboardData(win32con.CF_UNICODETEXT) 
            clip.CloseClipboard() 
        else:
            clip = gtk.clipboard_get(selection='PRIMARY')
            text = clip.wait_for_text()
        if text:
            text = text.strip()
            if common.is_url(text):
                entry.set_text(text)
        dlg.show_all()
        response = dlg.run()
        if response == gtk.RESPONSE_OK:
            url = entry.get_text().decode("utf_8")
            dlg.destroy()
            self.interactive_add_torrent_url(url) 
        else:
            dlg.destroy()

    def remove_torrent_clicked(self, obj=None):
        glade = gtk.glade.XML(common.get_glade_file("dgtkpopups.glade"), 
                    domain='deluge')
        asker = glade.get_widget("remove_torrent_dlg")
        if not common.windows_check():
            asker.set_icon(common.get_logo(18))
        asker.set_transient_for(self.window)

        warning = glade.get_widget("warning")
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
        self.tab_details.clear()

    def remove_toggle_warning(self, args, warning):
        if not args.get_active():
            warning.set_text(" ")
        else:
            warning.set_markup("<i>" + _("Warning - all downloaded files for \
this torrent will be deleted!") + "</i>")
        return False

    def update_tracker(self, obj=None):
        unique_ids = self.get_selected_torrent_rows()
        for uid in unique_ids:
            self.manager.update_tracker(uid)

    def scrape_tracker(self, obj=None):
        unique_ids = self.get_selected_torrent_rows()
        for uid in unique_ids:
            self.manager.scrape_tracker(uid)
    
    def clear_finished(self, obj=None):
        print "Clearing completed torrents"
        if dialogs.show_popup_question(self.window, _("Are you sure that you \
want to remove all seeding torrents?")):
            self.manager.clear_completed()
            self.update()
        
    def select_all_torrents(self, widget):
        self.torrent_view.get_selection().select_all()
    
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
        else:
            self.wtree.get_widget("tb_left").hide()
    
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
        self.wtree.get_widget("chk_infopane").set_active(self.config.get(
            "show_infopane"))
        self.wtree.get_widget("chk_toolbar").set_active(self.config.get(
            "show_toolbar"))
        self.wtree.get_widget("chk_size").set_active(self.config.get(
            "show_size"))
        self.wtree.get_widget("chk_status").set_active(self.config.get(
            "show_status"))
        self.wtree.get_widget("chk_seed").set_active(self.config.get(
            "show_seeders"))
        self.wtree.get_widget("chk_peer").set_active(self.config.get(
            "show_peers"))
        self.wtree.get_widget("chk_download").set_active(self.config.get(
            "show_dl"))
        self.wtree.get_widget("chk_upload").set_active(self.config.get("show_ul"))
        self.wtree.get_widget("chk_eta").set_active(self.config.get("show_eta"))
        self.wtree.get_widget("chk_availability").set_active(self.config.get(
            "show_availability"))
        self.wtree.get_widget("chk_ratio").set_active(self.config.get(
            "show_share"))
        self.wtree.get_widget("vpaned1").set_position(self.config.get(
            "window_height") - self.config.get("window_pane_position"))
    
    def save_window_settings(self):
        self.config.set("show_infopane", self.wtree.get_widget("chk_infopane").\
            get_active())
        self.config.set("show_toolbar", self.wtree.get_widget("chk_toolbar").\
            get_active())
        self.config.set("show_size", self.wtree.get_widget("chk_size").\
            get_active())
        self.config.set("show_status", self.status_column.get_visible())
        self.config.set("show_seeders", self.seed_column.get_visible())
        self.config.set("show_peers", self.peer_column.get_visible())
        self.config.set("show_dl", self.dl_column.get_visible())
        self.config.set("show_ul", self.ul_column.get_visible())
        self.config.set("show_eta", self.eta_column.get_visible())
        self.config.set("show_availability", self.availability_column.\
            get_visible())
        self.config.set("show_share", self.share_column.get_visible())
        self.config.set("window_pane_position", self.config.get(
            "window_height") - self.wtree.get_widget("vpaned1").get_position())

    def save_column_widths(self):
        to_save = ["queue", "name", "size", "status", "seed", "peer", "dl", 
                    "ul", "eta", "availability", "share"]
        for columns in to_save:
            pref_name = columns + '_width'
            column = getattr(self, columns + '_column') 
            self.config.set(pref_name, column.get_width())

    # Saves the tabs order (except the 'Details' tab)
    def save_tabs_order(self):
        tabs_order = []
        num_tabs = self.notebook.get_n_pages()
        for i in range(1, num_tabs):
            tab = self.notebook.get_nth_page(i) 
            tabs_order.append(self.notebook.get_tab_label_text(tab))

        tabs_order_str = ':'.join(tabs_order)
        self.config.set('tabs_order', tabs_order_str)

    def load_tabs_order(self):
        tabs_order_str = self.config.get('tabs_order') or ""
        tabs_order = tabs_order_str.split(':')
        tabs = {}
        num_tabs = self.notebook.get_n_pages()
        for i in range(1, num_tabs):
            tab = self.notebook.get_nth_page(i)
            tab_title = self.notebook.get_tab_label_text(tab)
            tabs[tab_title] = tab

        i = 1
        for tab in tabs_order:
            if tab in tabs:
                self.notebook.reorder_child(tabs[tab], i)
                i = i + 1

    def window_configure_event(self, widget, event):
        if not self.config.get("window_maximized"):
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
        if self.config.get("window_maximized"):
            self.window.maximize()

    def close(self, widget, event):
        if self.config.get("close_to_tray") and self.config.get(
            "enable_system_tray") and self.has_tray:
            self.window.hide()
            return True
        else:
            self.quit()
        
    def quit(self, widget=None):
        if self.window.get_property("visible"):
            self.shutdown()
        else:
            if self.config.get("lock_tray"):
                self.unlock_tray("quitus")
            else:
                self.shutdown()

    def shutdown(self, *arg):
        gtk.quit_add(0, self.manager.quit)
        self.window.hide()
        self.save_column_widths()
        self.save_window_settings()
        self.save_tabs_order()
        self.config.save()
        self.plugins.shutdown_all_plugins()
        #for the sake of windows, hide tray_icon
        self.tray_icon.set_visible(False)
        gtk.main_quit()

## For testing purposes, create a copy of the interface
if __name__ == "__main__":
    interface = DelugeGTK()
    interface.start()
