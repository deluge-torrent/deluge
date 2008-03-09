#
# blocklist/gtkui.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# Copyright (C) 2008 Mark Stahler ('kramed') <markstahler@gmail.com>
 
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
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
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

import os
import pkg_resources    # access plugin egg
from deluge.log import LOG as log
import deluge.component    # for systray
import ui
import gtk, gobject

FORMATS =  {
       'gzmule': ["Emule IP list (GZip)", None],
       'spzip': ["SafePeer Text (Zipped)", None],
       'pgtext': ["PeerGuardian Text (Uncompressed)", None],
       'p2bgz': ["PeerGuardian P2B (GZip)", None]
} 

class GtkUI(ui.UI):
    def __init__(self, plugin_api, plugin_name):
        log.debug("Calling UI init")
        # Call UI constructor
        ui.UI.__init__(self, plugin_api, plugin_name)
        log.debug("Blocklist GtkUI plugin initalized..")
    
    def enable(self):
        self.plugin.register_hook("on_apply_prefs", self.apply_prefs)

        # Import File Format Readers from TorrentBlocklist
        #ui.client.block_list_get_formats(self.callback_load_formats) # cant marshal classobj objects - wtf

        # Update Blocked IP status bar number - BETTER METHOD TO FOLLOW 
        # emit a blocklsit import signal
        gobject.timeout_add(5000, self.get_ip_count)
        gobject.timeout_add(10000, self.get_ip_count)
        gobject.timeout_add(20000, self.get_ip_count)
        
        self.load_interface()
    
    def disable(self):
        deluge.component.get("StatusBar").remove_item(self.blocklist_status)
        self.plugin.deregister_hook("on_apply_prefs", self.apply_prefs)
        
    def get_pixmap(self, fname):
        """Returns a pixmap file included with plugin"""
        return pkg_resources.resource_filename("blocklist", os.path.join("data", fname))
                
    def add_status_icon(self, ip_count):
        try:
            deluge.component.get("StatusBar").remove_item(self.blocklist_status)
        except:
            pass
        # self, image=None, stock=None, text=None, callback=None
        self.blocklist_status = deluge.component.get("StatusBar").add_item(self.get_pixmap("blocklist16.png"), None, str(ip_count) + " Blocked IP Ranges ", None)
        
    def get_ip_count(self):
        ui.client.block_list_count_ips(self.add_status_icon)
        return False
    
    def start_import(self, widget, data=None):
        ui.client.block_list_import_list(None)
        log.debug('Blocklist: Import button')
        gobject.timeout_add(20000, self.get_ip_count)
        
    def download_list(self, widget, data=None):
        self.apply_prefs()
        ui.client.block_list_download_list(None)
        log.debug('Blocklist: Download button')
        
    def unload_interface(self):
        self.plugin.remove_preferences_page("Blocklist")
        
#    def get_active_text(combobox):
#        model = combobox.get_model()
#        active = combobox.get_active()
#        if active < 0:
#            return None
#        return model[active][0]
    
    def load_interface(self):
        log.debug("Beginning gtk pane initialization")
        self.blocklist_pref_page = gtk.VBox(False, 3)
        self.blocklist_pref_page.set_spacing(6)
        
        label = gtk.Label()
        label.set_markup('<b>' + 'General' + '</b>')

        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_NONE)
        
        alignment = gtk.Alignment(0.5, 0.5, 1, 1)
        alignment.set_padding(8, 5, 5, 5)
                
        table = gtk.Table(8, 2, False)
        table.set_col_spacings(8)
        table.set_row_spacings(10)

        # First row
        label0 = gtk.Label()
        label0.set_text('Blocklist Type') 
        
        ls = gtk.ListStore(gobject.TYPE_STRING,  # Long name
                           gobject.TYPE_STRING)  # Short name
         
        self.listtype = gtk.ComboBox(model=ls)
        cell = gtk.CellRendererText()
        cell.set_property('xpad', 5) # padding for status text
        self.listtype.pack_start(cell, False)
        self.listtype.add_attribute(cell, 'text', 0)

        for k in FORMATS.keys():
            i = ls.append([FORMATS[k][0], k])
            FORMATS[k][1] = ls.get_path(i)        

        self.listtype.set_active(0)

        table.attach(label0, 0, 1, 0 , 1)
        table.attach(self.listtype, 1, 2, 0, 1)

        # Second row
        label1 = gtk.Label()
        label1.set_text('Blocklist URL')
        
        self.url = gtk.Entry()
        
        table.attach(label1, 0, 1, 1, 2)
        table.attach(self.url, 1, 2, 1, 2)
                  
        # Third row
        label2 = gtk.Label()
        label2.set_text('Check for a new blocklist every')
        
        self.check_after_days = gtk.SpinButton(None, 1.0, 0)
        self.check_after_days.set_increments(1, 3)
        self.check_after_days.set_range(-1, 14)
        
        label3 = gtk.Label()
        label3.set_text('days')
        
        hbox = gtk.HBox(False, 3)
        hbox.pack_start(label2, False, True)
        hbox.pack_start(self.check_after_days, False, False, 4)
        hbox.pack_start(label3)
        
        alignment.add(table)
        table.attach(hbox, 0, 2, 2, 3)
        
        # Fourth row
        label4 = gtk.Label()
        label4.set_text('Timeout to download new blocklist')
        
        self.timeout = gtk.SpinButton(None, 5.0, 0)
        self.timeout.set_increments(5, 20)
        self.timeout.set_range(15, 360)
        
        label5 = gtk.Label()
        label5.set_text('seconds')
        
        hbox1 = gtk.HBox(False, 3)
        hbox1.pack_start(label4, False, True)
        hbox1.pack_start(self.timeout)
        hbox1.pack_start(label5, False, True)
        
        table.attach(hbox1, 0, 2, 3, 4)
        
        # Fifth row
        label5 = gtk.Label()
        label5.set_text('Times to attempt download of new list')
                
        self.try_times = gtk.SpinButton(None, 1.0, 0)
        self.try_times.set_increments(1, 2)
        self.try_times.set_range(1, 5)
        
        hbox2 = gtk.HBox(False, 3)
        hbox2.pack_start(label5, False, True)
        hbox2.pack_start(self.try_times)
        
        table.attach(hbox2, 0, 2, 4, 5)

        # sixth row        
        self.load_on_start = gtk.CheckButton('Import blocklist on daemon startup')
        table.attach(self.load_on_start, 0, 2, 5, 6)
        
        # download new list button
        download_button = gtk.Button("_Download Blocklist", None, True)
        download_button.connect("clicked", self.download_list, None)
        
        pixbuf = gtk.gdk.pixbuf_new_from_file(self.get_pixmap("blocklist_download24.png"))
        image = gtk.image_new_from_pixbuf(pixbuf)
        download_button.set_image(image)
        table.attach(download_button, 0, 2, 6, 7)
        
        # import button (Check and possibly download)
        import_button = gtk.Button("_Import Blocklist", None, True)
        import_button.connect("clicked", self.start_import, None)
        
        pixbuf = gtk.gdk.pixbuf_new_from_file(self.get_pixmap("blocklist_import24.png"))
        image = gtk.image_new_from_pixbuf(pixbuf)
        import_button.set_image(image)
        
        table.attach(import_button, 0, 2, 7, 8)
        
        
        # finish frame
        frame.set_label_widget(label)
        frame.add(alignment)
        
        self.blocklist_pref_page.pack_start(frame)
        
        # Add preferences page to preferences page
        log.debug('Adding Blocklist Preferences page')
        self.plugin.add_preferences_page("Blocklist", self.blocklist_pref_page)
        
        # Load settings from config and fill widgets with settings
        log.debug('Starting to load blocklist preferences')      
        self.fetch_prefs()
        log.debug('Finished loading blocklist preferences')
                
                
    def fetch_prefs(self):    # Fetch settings dictionary from plugin core and pass it to GTK ui settings
        log.info('Blocklist: Fetching and loading Preferences via GTK ui')
        ui.client.block_list_get_options(self.callback_load_prefs)
        
    def apply_prefs(self):
        log.info('Blocklist: Preferences saved via Gtk ui')
        settings_dict = {
                         "url": self.url.get_text(),
                         "listtype": self.get_ltype(),
                         "check_after_days": self.check_after_days.get_value_as_int(),
                         "load_on_start":self.load_on_start.get_active(),
                         "try_times": self.try_times.get_value_as_int(),
                         "timeout": self.timeout.get_value_as_int()   
                         }
        ui.client.block_list_set_options(None, settings_dict)
        # Needs to go in another thread or wait until window is closed
        #gobject.idle_add(self.call_critical_setting)
    
    def call_critical_setting(self):
        ui.client.block_list_critical_setting(None)        # This checks to see if url or listtype changed, if so download & import
        self.get_ip_count()
        
    # GTK Gui Callback functions    
    def callback_load_prefs(self, dict):
        log.info('Blocklist: Callback Load Prefs GTK ui')
        self.settings_url(dict['url'])
        self.settings_listtype(dict['listtype'])
        self.settings_load(dict['load_on_start'])
        self.settings_check_after_days(dict['check_after_days'])
        self.settings_timeout(dict['timeout'])
        self.settings_try_times(dict['try_times'])
            
    # Specific function to return proper listtype so we can save and open it again
    def get_ltype(self):
        ls = self.listtype.get_model()
        log.debug(ls)
        ltype = ls[self.listtype.get_active()][1]
        log.debug(ltype)
        return ltype
    
    # Settings functions
    def settings_listtype(self, setting):
        log.debug('Blocklist: listtype')
        path = FORMATS[setting][1]
        i = self.listtype.get_model().get_iter(path)
        self.listtype.set_active_iter(i)    
                
    def settings_url(self, setting):
        log.debug('Blocklist: url')
        self.url.set_text(setting)

    def settings_check_after_days(self, setting):
        log.debug('Blocklist: days')
        self.check_after_days.set_value(setting)
        
    def settings_load(self, setting):
        log.debug('Blocklist: load_on_start')
        log.info(setting)
        if setting == True or setting == "True":
            setting = 1
        else:
            setting = 0
        self.load_on_start.set_active(setting)
        
    def settings_timeout(self, setting):
        log.debug('Blocklist: timeout')
        self.timeout.set_value(setting)
        
    def settings_try_times(self, setting):
        log.debug('Blocklist: try times')
        self.try_times.set_value(setting)

        