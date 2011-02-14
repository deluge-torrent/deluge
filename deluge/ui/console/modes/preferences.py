# -*- coding: utf-8 -*-
#
# preferences.py
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
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

import deluge.component as component
from deluge.ui.client import client
from basemode import BaseMode
from input_popup import SelectInput

from preference_panes import DownloadsPane,NetworkPane,BandwidthPane,InterfacePane
from preference_panes import OtherPane,DaemonPane,QueuePane,ProxyPane,CachePane

from collections import deque

try:
    import curses
except ImportError:
    pass


import logging
log = logging.getLogger(__name__)

class ZONE:
    CATEGORIES = 0
    PREFRENCES = 1
    ACTIONS = 2

class Preferences(BaseMode):
    def __init__(self, parent_mode, core_config, stdscr, encoding=None):
        self.parent_mode = parent_mode
        self.categories = [_("Downloads"), _("Network"), _("Bandwidth"),
                           _("Interface"), _("Other"), _("Daemon"), _("Queue"), _("Proxy"),
                           _("Cache")] # , _("Plugins")]
        self.cur_cat = 0
        self.popup = None
        self.messages = deque()
        self.action_input = None

        self.core_config = core_config

        self.active_zone = ZONE.CATEGORIES

        # how wide is the left 'pane' with categories
        self.div_off = 15

        BaseMode.__init__(self, stdscr, encoding, False)

        # create the panes
        self.prefs_width = self.cols-self.div_off-1
        self.panes = [
            DownloadsPane(self.div_off+2, self, self.prefs_width),
            NetworkPane(self.div_off+2, self, self.prefs_width),
            BandwidthPane(self.div_off+2, self, self.prefs_width),
            InterfacePane(self.div_off+2, self, self.prefs_width),
            OtherPane(self.div_off+2, self, self.prefs_width),
            DaemonPane(self.div_off+2, self, self.prefs_width),
            QueuePane(self.div_off+2, self, self.prefs_width),
            ProxyPane(self.div_off+2, self, self.prefs_width),
            CachePane(self.div_off+2, self, self.prefs_width)
            ]

        self.action_input = SelectInput(self,None,None,["Cancel","Apply","OK"],[0,1,2],0)
        self.refresh()

    def __draw_catetories(self):
        for i,category in enumerate(self.categories):
            if i == self.cur_cat and self.active_zone == ZONE.CATEGORIES:
                self.add_string(i+1,"- {!black,white,bold!}%s"%category,pad=False)
            elif i == self.cur_cat:
                self.add_string(i+1,"- {!black,white!}%s"%category,pad=False)
            else:
                self.add_string(i+1,"- %s"%category)
        self.stdscr.vline(1,self.div_off,'|',self.rows-2)

    def __draw_preferences(self):
        self.panes[self.cur_cat].render(self,self.stdscr, self.prefs_width, self.active_zone == ZONE.PREFRENCES)

    def __draw_actions(self):
        selected = self.active_zone == ZONE.ACTIONS
        self.stdscr.hline(self.rows-3,self.div_off+1,"_",self.cols)
        self.action_input.render(self.stdscr,self.rows-2,self.cols,selected,self.cols-22)
    
    def refresh(self):
        if self.popup == None and self.messages:
            title,msg = self.messages.popleft()
            self.popup = MessagePopup(self,title,msg)

        self.stdscr.clear()
        self.add_string(0,self.statusbars.topbar)
        hstr =  "%sPress [h] for help"%(" "*(self.cols - len(self.statusbars.bottombar) - 10))
        self.add_string(self.rows - 1, "%s%s"%(self.statusbars.bottombar,hstr))

        self.__draw_catetories()
        self.__draw_actions()

        # do this last since it moves the cursor
        self.__draw_preferences()
        
        self.stdscr.noutrefresh()

        if self.popup:
            self.popup.refresh()

        curses.doupdate()

    def __category_read(self, c):
        # Navigate prefs
        if c == curses.KEY_UP:
            self.cur_cat = max(0,self.cur_cat-1)
        elif c == curses.KEY_DOWN:
            self.cur_cat = min(len(self.categories)-1,self.cur_cat+1)

    def __prefs_read(self, c):
        self.panes[self.cur_cat].handle_read(c)

    def __apply_prefs(self):
        new_core_config = {}
        for pane in self.panes:
            pane.add_config_values(new_core_config)
        # Apply Core Prefs
        if client.connected():
            # Only do this if we're connected to a daemon
            config_to_set = {}
            for key in new_core_config.keys():
                # The values do not match so this needs to be updated
                if self.core_config[key] != new_core_config[key]:
                    config_to_set[key] = new_core_config[key]

            if config_to_set:
                # Set each changed config value in the core
                client.core.set_config(config_to_set)
                client.force_call(True)
                # Update the configuration
                self.core_config.update(config_to_set)

    def __update_preferences(self,core_config):
        self.core_config = core_config
        for pane in self.panes:
            pane.update_values(core_config)

    def __actions_read(self, c):
        self.action_input.handle_read(c)
        if c == curses.KEY_ENTER or c == 10:
            # take action
            if self.action_input.selidx == 0: # cancel
                self.back_to_parent()
            elif self.action_input.selidx == 1: # apply
                self.__apply_prefs()
                client.core.get_config().addCallback(self.__update_preferences)
            elif self.action_input.selidx == 2: #  OK
                self.__apply_prefs()
                self.back_to_parent()
                

    def back_to_parent(self):
        self.stdscr.clear()
        component.get("ConsoleUI").set_mode(self.parent_mode)
        self.parent_mode.resume()

    def _doRead(self):
        c = self.stdscr.getch()

        if self.popup:
            if self.popup.handle_read(c):
                self.popup = None
            self.refresh()
            return

        if c > 31 and c < 256:
            if chr(c) == 'Q':
                from twisted.internet import reactor
                if client.connected():
                    def on_disconnect(result):
                        reactor.stop()
                    client.disconnect().addCallback(on_disconnect)
                else:
                    reactor.stop()            
                return

        if c == 9:
            self.active_zone += 1
            if self.active_zone > ZONE.ACTIONS:
                self.active_zone = ZONE.CATEGORIES

        elif c == curses.KEY_BTAB:
            self.active_zone -= 1
            if self.active_zone < ZONE.CATEGORIES:
                self.active_zone = ZONE.ACTIONS

        else:
            if self.active_zone == ZONE.CATEGORIES:
                self.__category_read(c)
            elif self.active_zone == ZONE.PREFRENCES:
                self.__prefs_read(c)
            elif self.active_zone == ZONE.ACTIONS:
                self.__actions_read(c)

        self.refresh()


