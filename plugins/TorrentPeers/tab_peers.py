from itertools import izip
from deluge import dgtk
from deluge import common
import gobject
import gtk
class PeersTabManager(object):
    def __init__(self, peer_view, manager):
        self.peer_view = peer_view
        self.manager = manager
        self.peer_unique_id = None
        # IP int, IP string, Client, Percent Complete, Down Speed, Up Speed
        # IP int is for faster sorting
        self.peer_store = gtk.ListStore(gobject.TYPE_UINT, gtk.gdk.Pixbuf, 
                                        str, str, float, int, int)
        # Stores IP -> gtk.TreeIter's iter mapping for quick look up 
        # in update_torrent_info_widget
        self.peer_store_dict = {}       
        self._cached_flags = {}
        self.show_flags = None
        self.flag_size = ""

    def clear_peer_store(self):
        self.peer_store.clear()
        self.peer_store_dict = {}

    def set_unique_id(self, unique_id):
        self.peer_unique_id = unique_id

    def build_peers_view(self):
        def percent(column, cell, model, iter, data):
            percent = float(model.get_value(iter, data))
            percent_str = "%.2f%%"%percent
            cell.set_property("text", percent_str)

        self.peer_view.set_model(self.peer_store)
        
        ip_column = dgtk.add_texticon_column(self.peer_view, _("IP Address"), 
                                             1, 2)
        ip_column.set_sort_column_id(0)
        dgtk.add_text_column(self.peer_view, _("Client"), 3)
        dgtk.add_func_column(self.peer_view, _("Percent Complete"), percent, 
                             4)
        dgtk.add_func_column(self.peer_view, _("Down Speed"), 
                             dgtk.cell_data_speed, 5)
        dgtk.add_func_column(self.peer_view, _("Up Speed"), 
                             dgtk.cell_data_speed, 6)

    def enable_flags(self):
        self.show_flags = True

    def disable_flags(self):
        self.show_flags = False

    def clear_flag_cache(self):
        self._cached_flags = {}

    def set_flag_size(self, size):
        self.flag_size = size

    def get_country_flag_image(self, country):
        flag_image = None
        if self.show_flags and country.isalpha():
            if country in self._cached_flags:
                flag_image = self._cached_flags[country]
            else:
                try:
                    flag_path = "flags" + self.flag_size + '/' + str(country.lower()) + '.png'
                    flag_image = gtk.gdk.pixbuf_new_from_file(
                                        common.get_pixmap(flag_path))
                except gobject.GError:
                    pass
                    
                self._cached_flags[country] = flag_image
            
        return flag_image
        
    def update_peer_store(self):
        new_peer_info = self.manager.get_torrent_peer_info(self.peer_unique_id)
        new_ips = set()
        
        for peer in new_peer_info:
            # Update peers already in peers list
            if peer['ip'] in self.peer_store_dict:
                iter = self.peer_store_dict[peer['ip']]

                dgtk.update_store(self.peer_store, iter, (1, 4, 5, 6),
                                  (self.get_country_flag_image(peer["country"]),
                                   round(peer["peer_has"], 2),
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

                    client = peer["client"]
                    try:
                        client = client.decode('utf-8')
                    except UnicodeDecodeError:
                        # Fallback to latin-1 in case peer's client 
                        # doesn't use utf-8. utorrent < 1.7 for example
                        client = client.decode('latin-1')

                    iter = self.peer_store.append([ip_int, 
                               self.get_country_flag_image(peer["country"]), 
                               peer["ip"], client, round(peer["peer_has"], 2),
                               peer["download_speed"], peer["upload_speed"]])

                    self.peer_store_dict[peer['ip']] = iter
        
        # Remove peers that no longer exist in new_ips
        for ip in set(self.peer_store_dict.keys()).difference(new_ips):
            self.peer_store.remove(self.peer_store_dict[ip])
            del self.peer_store_dict[ip]
