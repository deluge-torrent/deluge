#
# blocklist/core.py
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

from torrentblocklist import TorrentBlockList
from deluge.log import LOG as log
from deluge.plugins.corepluginbase import CorePluginBase

class Core(CorePluginBase):    
    def enable(self):
        self.blocklist = TorrentBlockList(self.plugin)
        self.plugin.register_hook("post_session_load", self._post_session_load)           
        log.debug('Blocklist: Plugin enabled..')
    
    def disable(self):
        log.debug('Blocklist: Plugin disabled')
        self.plugin.deregister_hook("post_session_load", self._post_session_load)
        self.plugin.reset_ip_filter()
        # Delete the blocklist object
        del self.blocklist
        self.blocklist = None
        
    def update(self):
        pass
    
    ## Hooks for core ##
    def _post_session_load(self):
        log.info('Blocklist: Session load hook caught')
        if self.blocklist.load_on_start == True:
            # Wait until an idle time to load block list
            import gobject
            gobject.idle_add(self.blocklist.import_list)
            
    ## Callbacks
    def register_import_hook(self):
        self.plugin.register_hook("post_session_load", self._post_session_load)
        return False
            
    # Exported functions for ui
    def export_critical_setting(self):
        if self.blocklist.old_url != self.blocklist.url or self.blocklist.old_listtype != self.blocklist.listtype:
            log.info('Blocklist: Critical setting changed')
            self.blocklist.download()
            self.blocklist.import_list()
            self.blocklist.return_count()        # Return count after import
        
        # New settings are now old settings
        self.blocklist.old_url = self.blocklist.url
        self.blocklist.old_listtype = self.blocklist.listtype
        
    def export_count_ips(self):
        log.debug('Blocklist: Count IPs imported into blocklist')
        return self.blocklist.return_count()
    
    def export_import_list(self):
        log.debug('Blocklist: Import started from GTK UI')
        self.blocklist.import_list()
        
    def export_download_list(self):
        log.debug('Blocklist: Download started from GTK UI')
        force_check = True
        self.blocklist.check_update(force_check)
        # Initialize download attempt
        self.blocklist.attempt = 0
        
        if self.blocklist.fetch == True:
            self.blocklist.download()

    
    def export_set_options(self, settings):
        log.debug("Blocklist: Set Options")
        self.blocklist.set_options(settings)
        
    def export_get_options(self):
        log.debug("Blocklist: Get Options")
        settings_dict = {   
                         "url": self.blocklist.url,
                         "listtype": self.blocklist.listtype,
                         "check_after_days": self.blocklist.check_after_days,
                         "load_on_start":self.blocklist.load_on_start,
                         "try_times": self.blocklist.try_times,
                         "timeout": self.blocklist.timeout   
                         }
        log.info(settings_dict)
        return settings_dict
    
    def export_get_config_value(self, key):
        log.debug("Blocklist: Get configuration setting")
        return self.blocklist.get_config_value(key)
    
    def export_set_config_value(self, key):
        log.debug("Blocklist: Set configuration setting")
        return self.blocklist.set_config_value(key)
    
    def export_get_formats(self):
        log.debug('Blocklist: Get Reader Formats')
        return self.blocklist.return_formats()

    