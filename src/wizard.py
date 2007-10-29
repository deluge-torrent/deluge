"""
this is our wizard which aids configuration for new users
"""
# -*- coding: utf-8 -*-
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

class WizardGTK:
    """
    the main window for our configuration wizard
    """
    def __init__(self):
        import gtk
        import gtk.glade
        import os
        import deluge
        import deluge.common
        import deluge.pref
        self.wtree = gtk.glade.XML(deluge.common.get_glade_file("wizard.glade")\
            , domain='deluge')
        self.wtree.signal_autoconnect({'apply_prefs': self.apply_prefs,
                                'cancel': self.cancel,
                                'toggle': self.toggle,
                                'close': self.cancel})
        #add deluge logo to headers
        self.window = self.wtree.get_widget("wizard")
        pixmap = deluge.common.get_logo(48)
        self.window.set_page_header_image(self.wtree.get_widget('label1'), \
            pixmap)
        self.window.set_page_header_image(self.wtree.get_widget('vbox1'), \
            pixmap)
        self.window.set_page_header_image(self.wtree.get_widget('vbox2'), \
            pixmap)
        self.window.set_page_header_image(self.wtree.get_widget('vbox3'), \
            pixmap)
        self.window.set_page_header_image(self.wtree.get_widget\
            ('chk_send_info'), pixmap)

        #activate forward buttons for all pages
        self.window.set_page_complete(self.wtree.get_widget('label1'), True)
        self.window.set_page_complete(self.wtree.get_widget('vbox1'), True)
        self.window.set_page_complete(self.wtree.get_widget('vbox2'), True)
        self.window.set_page_complete(self.wtree.get_widget('vbox3'), True)
        self.window.set_page_complete(self.wtree.get_widget('chk_send_info'), \
            True)
        config_file = deluge.common.CONFIG_DIR + "/prefs.state"
        self.config = deluge.pref.Preferences(config_file, False, 
            defaults={"listen_on" : [6881,6889],
                    "send_info": True,
                    "random_port": False,
                    "max_half_open" : 8,
                    "max_active_torrents" : 8,
                    "max_upload_slots_global" : 15,
                    "max_connections_global" : 200,
                    "max_upload_speed" : -1,
                    "default_download_path" : os.path.expanduser("~/"),
                    "use_default_dir" : False
                    })
        try:
            self.config.load()
        except IOError:
            pass
        else:
            self.wtree.get_widget('spin_port_min').set_value(self.config.\
                get("listen_on")[0])
            self.wtree.get_widget('spin_port_max').set_value(self.config.\
                get("listen_on")[1])
            self.wtree.get_widget('chk_send_info').set_active(self.config.\
                get("send_info"))
            self.wtree.get_widget('chk_random_ports').set_active(self.config.\
                get("random_port"))
            self.wtree.get_widget('radio_save_all_to').set_active(self.config.\
                get("use_default_dir"))
            self.wtree.get_widget('download_path_button').set_filename(self.\
                config.get("default_download_path"))
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                self.config.get("max_connections_global"))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                self.config.get("max_upload_slots_global"))
            self.wtree.get_widget('spin_max_upload').set_value(self.config.\
                get("max_upload_speed"))
            self.wtree.get_widget('spin_torrents').set_value(self.config.\
                get("max_active_torrents"))
            self.wtree.get_widget('spin_max_half_open').set_value(self.config.\
                get("max_half_open"))

        #show wizard
        self.window.show()
        gtk.main()

    def toggle(self, *args):
        """
        updates the gui with preferences according to user input
        """
        self.wtree.get_widget('spin_port_min').set_sensitive(
            not self.wtree.get_widget('chk_random_ports').get_active())
        self.wtree.get_widget('spin_port_max').set_sensitive(
            not self.wtree.get_widget('chk_random_ports').get_active())
        if self.wtree.get_widget('combo_upload_line').get_active_text() == \
                "28k":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('25'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('1'))
            self.wtree.get_widget('spin_max_upload').set_value(float('2'))
            self.wtree.get_widget('spin_torrents').set_value(float('1'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "56k":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('30'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('3'))
            self.wtree.get_widget('spin_max_upload').set_value(float('2'))
            self.wtree.get_widget('spin_torrents').set_value(float('1'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "64k":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('75'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('2'))
            self.wtree.get_widget('spin_max_upload').set_value(float('5'))
            self.wtree.get_widget('spin_torrents').set_value(float('1'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "96k":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('75'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('3'))
            self.wtree.get_widget('spin_max_upload').set_value(float('7'))
            self.wtree.get_widget('spin_torrents').set_value(float('1'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "128k":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('88'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('3'))
            self.wtree.get_widget('spin_max_upload').set_value(float('9'))
            self.wtree.get_widget('spin_torrents').set_value(float('1'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "192k":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('90'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('3'))
            self.wtree.get_widget('spin_max_upload').set_value(float('17'))
            self.wtree.get_widget('spin_torrents').set_value(float('1'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "256k":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('130'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('3'))
            self.wtree.get_widget('spin_max_upload').set_value(float('22'))
            self.wtree.get_widget('spin_torrents').set_value(float('1'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "384k":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('230'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('4'))
            self.wtree.get_widget('spin_max_upload').set_value(float('35'))
            self.wtree.get_widget('spin_torrents').set_value(float('3'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "512k":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('250'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('4'))
            self.wtree.get_widget('spin_max_upload').set_value(float('47'))
            self.wtree.get_widget('spin_torrents').set_value(float('3'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "640k":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('375'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('4'))
            self.wtree.get_widget('spin_max_upload').set_value(float('60'))
            self.wtree.get_widget('spin_torrents').set_value(float('4'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "768k":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('450'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('5'))
            self.wtree.get_widget('spin_max_upload').set_value(float('72'))
            self.wtree.get_widget('spin_torrents').set_value(float('5'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "1Mbit":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('600'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('6'))
            self.wtree.get_widget('spin_max_upload').set_value(float('92'))
            self.wtree.get_widget('spin_torrents').set_value(float('5'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "2Mbit":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('750'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('8'))
            self.wtree.get_widget('spin_max_upload').set_value(float('186'))
            self.wtree.get_widget('spin_torrents').set_value(float('9'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "10Mbit":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('800'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('25'))
            self.wtree.get_widget('spin_max_upload').set_value(float('1120'))
            self.wtree.get_widget('spin_torrents').set_value(float('15'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "20Mbit":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('850'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('30'))
            self.wtree.get_widget('spin_max_upload').set_value(float('2240'))
            self.wtree.get_widget('spin_torrents').set_value(float('15'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "40Mbit":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('900'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('35'))
            self.wtree.get_widget('spin_max_upload').set_value(float('4480'))
            self.wtree.get_widget('spin_torrents').set_value(float('15'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "50Mbit":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('950'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('50'))
            self.wtree.get_widget('spin_max_upload').set_value(float('5600'))
            self.wtree.get_widget('spin_torrents').set_value(float('20'))
        elif self.wtree.get_widget('combo_upload_line').get_active_text() == \
            "100Mbit":
            self.wtree.get_widget('spin_max_connections_global').set_value(\
                float('1000'))
            self.wtree.get_widget('spin_max_upload_slots_global').set_value(\
                float('50'))
            self.wtree.get_widget('spin_max_upload').set_value(float('11200'))
            self.wtree.get_widget('spin_torrents').set_value(float('25'))

    def create_file(self):
        """
        creates file that we check for to know if we need to run the wizard or
        not
        """
        import os
        import deluge.common
        firstrun = open(os.path.join(deluge.common.CONFIG_DIR, 'firstrun'), 'w')
        firstrun.write("")
        firstrun.close()

    def cancel(self, *args):
        """
        exits the wizard and creates file so we dont re-run
        """
        import gtk
        self.create_file()
        self.window.destroy()
        gtk.main_quit()

    def apply_prefs(self, *args):
        """
        saves configuration settings
        """
        import gtk
        self.create_file()
        self.config.set("random_port", self.wtree.get_widget('chk_random_ports'\
            ).get_active())
        self.config.set("listen_on", [self.wtree.get_widget("spin_port_min")\
            .get_value(), self.wtree.get_widget("spin_port_max").get_value()])
        self.config.set("send_info", self.wtree.get_widget("chk_send_info").\
            get_active())
        self.config.set("max_connections_global", int(self.wtree.get_widget\
            ('spin_max_connections_global').get_value()))
        self.config.set("max_upload_slots_global", int(self.wtree.get_widget\
            ('spin_max_upload_slots_global').get_value()))
        self.config.set("max_upload_speed", int(self.wtree.get_widget(\
            'spin_max_upload').get_value()))
        self.config.set("max_active_torrents", int(self.wtree.get_widget(\
            'spin_torrents').get_value()))
        self.config.set("max_half_open", int(self.wtree.get_widget(\
            'spin_max_half_open').get_value()))
        self.config.set("use_default_dir", self.wtree.get_widget(\
            'radio_save_all_to').get_active())
        self.config.set("default_download_path", self.wtree.get_widget(\
            'download_path_button').get_filename())
        self.config.save()
        gtk.main_quit()
