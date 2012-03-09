# -*- coding: utf-8 -*-
#
# popup.py
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

try:
    import curses
    import signal
except ImportError:
    pass

import format_utils
import logging
log = logging.getLogger(__name__)

class Popup:
    def __init__(self,parent_mode,title,width_req=-1,height_req=-1,close_cb=None,init_lines=None):
        """
        Init a new popup.  The default constructor will handle sizing and borders and the like.

        NB: The parent mode is responsible for calling refresh on any popups it wants to show.
            This should be called as the last thing in the parents refresh method.

            The parent *must* also call _doRead on the popup instead of/in addition to
            running its own _doRead code if it wants to have the popup handle user input.

        :param parent_mode: must be a basemode (or subclass) which the popup will be drawn over
        :parem title: string, the title of the popup window

        Popups have two methods that must be implemented:

        refresh(self) - draw the popup window to screen.  this default mode simply draws a bordered window
                        with the supplied title to the screen

        add_string(self, row, string) - add string at row.  handles triming/ignoring if the string won't fit in the popup

        _doRead(self) - handle user input to the popup.
        """
        self.parent = parent_mode

        if (height_req <= 0):
            height_req = int(self.parent.rows/2)
        if (width_req <= 0):
            width_req = int(self.parent.cols/2)
        by = (self.parent.rows/2)-(height_req/2)
        bx = (self.parent.cols/2)-(width_req/2)
        self.screen = curses.newwin(height_req,width_req,by,bx)

        self.title = title
        self.close_cb = close_cb
        self.height,self.width = self.screen.getmaxyx()
        self.divider = None
        self.lineoff = 0
        if init_lines:
            self._lines = init_lines
        else:
            self._lines = []

    def _refresh_lines(self):
        crow = 1
        for line in self._lines[self.lineoff:]:
            if (crow >= self.height-1):
                break
            self.parent.add_string(crow,line,self.screen,1,False,True)
            crow+=1

    def handle_resize(self):
        log.debug("Resizing popup window (actually, just creating a new one)")
        self.screen = curses.newwin((self.parent.rows/2),(self.parent.cols/2),(self.parent.rows/4),(self.parent.cols/4))
        self.height,self.width = self.screen.getmaxyx()


    def refresh(self):
        self.screen.clear()
        self.screen.border(0,0,0,0)
        toff = max(1,int((self.parent.cols/4)-(len(self.title)/2)))
        self.parent.add_string(0,"{!white,black,bold!}%s"%self.title,self.screen,toff,False,True)

        self._refresh_lines()
        if (len(self._lines) > (self.height-2)):
            lts = len(self._lines)-(self.height-3)
            perc_sc = float(self.lineoff)/lts
            sb_pos = int((self.height-2)*perc_sc)+1
            if (sb_pos == 1) and (self.lineoff != 0):
                sb_pos += 1
            self.parent.add_string(sb_pos, "{!white,black,bold!}|",self.screen,col=(self.width-1),pad=False,trim=False)

        self.screen.redrawwin()
        self.screen.noutrefresh()

    def clear(self):
        self._lines = []

    def handle_read(self, c):
        if c == curses.KEY_UP:
            self.lineoff = max(0,self.lineoff -1)
        elif c == curses.KEY_DOWN:
            if len(self._lines)-self.lineoff > (self.height-2):
                self.lineoff += 1

        elif c == curses.KEY_ENTER or c == 10 or c == 27: # close on enter/esc
            if self.close_cb:
                self.close_cb()
            return True # close the popup

        if c > 31 and c < 256 and chr(c) == 'q':
            if self.close_cb:
                self.close_cb()
            return True # close the popup

        self.refresh()

        return False

    def set_title(self, title):
        self.title = title

    def add_line(self, string):
        self._lines.append(string)

    def add_divider(self):
        if not self.divider:
            self.divider = "-"*(self.width-2)
        self._lines.append(self.divider)


class SelectablePopup(Popup):
    """
    A popup which will let the user select from some of the lines that
    are added.
    """
    def __init__(self,parent_mode,title,selection_callback,*args):
        Popup.__init__(self,parent_mode,title)
        self._selection_callback = selection_callback
        self._selection_args = args
        self._selectable_lines = []
        self._select_data = []
        self._line_foregrounds = []
        self._udxs = {}
        self._hotkeys = {}
        self._selected = -1

    def add_line(self, string, selectable=True, use_underline=True, data=None, foreground=None):
        if use_underline:
            udx = string.find('_')
            if udx >= 0:
                string = string[:udx]+string[udx+1:]
                self._udxs[len(self._lines)+1] = udx
                c = string[udx].lower()
                self._hotkeys[c] = len(self._lines)
        Popup.add_line(self,string)
        self._line_foregrounds.append(foreground)
        if selectable:
            self._selectable_lines.append(len(self._lines)-1)
            self._select_data.append(data)
            if self._selected < 0:
                self._selected = (len(self._lines)-1)

    def _refresh_lines(self):
        crow = 1
        for row,line in enumerate(self._lines):
            if (crow >= self.height-1):
                break
            if (row < self.lineoff):
                continue
            fg = self._line_foregrounds[row]
            udx = self._udxs.get(crow)
            if row == self._selected:
                if fg == None: fg = "black"
                colorstr = "{!%s,white,bold!}"%fg
                if udx >= 0:
                    ustr = "{!%s,white,bold,underline!}"%fg
            else:
                if fg == None: fg = "white"
                colorstr = "{!%s,black!}"%fg
                if udx >= 0:
                    ustr = "{!%s,black,underline!}"%fg
            if udx == 0:
                self.parent.add_string(crow,"- %s%c%s%s"%(ustr,line[0],colorstr,line[1:]),self.screen,1,False,True)
            elif udx > 0:
                # well, this is a litte gross
                self.parent.add_string(crow,"- %s%s%s%c%s%s"%(colorstr,line[:udx],ustr,line[udx],colorstr,line[udx+1:]),self.screen,1,False,True)
            else:
                self.parent.add_string(crow,"- %s%s"%(colorstr,line),self.screen,1,False,True)
            crow+=1

    def current_selection(self):
        "Returns a tuple of (selected index, selected data)"
        idx = self._selectable_lines.index(self._selected)
        return (idx,self._select_data[idx])

    def add_divider(self,color="white"):
        if not self.divider:
            self.divider = "-"*(self.width-6)+" -"
        self._lines.append(self.divider)
        self._line_foregrounds.append(color)

    def handle_read(self, c):
        if c == curses.KEY_UP:
            #self.lineoff = max(0,self.lineoff -1)
            if (self._selected != self._selectable_lines[0] and
                len(self._selectable_lines) > 1):
                idx = self._selectable_lines.index(self._selected)
                self._selected = self._selectable_lines[idx-1]
        elif c == curses.KEY_DOWN:
            #if len(self._lines)-self.lineoff > (self.height-2):
            #    self.lineoff += 1
            idx = self._selectable_lines.index(self._selected)
            if (idx < len(self._selectable_lines)-1):
                self._selected = self._selectable_lines[idx+1]
        elif c == 27: # close on esc, no action
            return True
        elif c == curses.KEY_ENTER or c == 10:
            idx = self._selectable_lines.index(self._selected)
            return self._selection_callback(idx,self._select_data[idx],*self._selection_args)
        if c > 31 and c < 256:
            if chr(c) == 'q':
                return True # close the popup
            uc = chr(c).lower()
            if uc in self._hotkeys:
                # exec hotkey action
                idx = self._selectable_lines.index(self._hotkeys[uc])
                return self._selection_callback(idx,self._select_data[idx],*self._selection_args)
        self.refresh()

        return False


class MessagePopup(Popup):
    """
    Popup that just displays a message
    """
    def __init__(self, parent_mode, title, message):
        self.message = message
        self.width= int(parent_mode.cols/2)
        lns = format_utils.wrap_string(self.message,self.width-2,3,True)
        hr = min(len(lns)+2,int(parent_mode.rows/2))
        Popup.__init__(self,parent_mode,title,height_req=hr)
        self._lines = lns

    def handle_resize(self):
        Popup.handle_resize(self)
        self.clear()
        self._lines = self._split_message()
