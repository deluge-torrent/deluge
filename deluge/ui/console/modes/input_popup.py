#
# input_popup.py
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# Complete function from commands/add.py:
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
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
except ImportError:
    pass

import logging,os.path

from popup import Popup

log = logging.getLogger(__name__)

def complete(line):
    line = os.path.abspath(os.path.expanduser(line))
    ret = []
    if os.path.exists(line):
        # This is a correct path, check to see if it's a directory
        if os.path.isdir(line):
            # Directory, so we need to show contents of directory
            #ret.extend(os.listdir(line))
            for f in os.listdir(line):
                # Skip hidden
                if f.startswith("."):
                    continue
                f = os.path.join(line, f)
                if os.path.isdir(f):
                    f += "/"
                ret.append(f)
        else:
            # This is a file, but we could be looking for another file that
            # shares a common prefix.
            for f in os.listdir(os.path.dirname(line)):
                if f.startswith(os.path.split(line)[1]):
                    ret.append(os.path.join( os.path.dirname(line), f))
    else:
        # This path does not exist, so lets do a listdir on it's parent
        # and find any matches.
        ret = []
        if os.path.isdir(os.path.dirname(line)):
            for f in os.listdir(os.path.dirname(line)):
                if f.startswith(os.path.split(line)[1]):
                    p = os.path.join(os.path.dirname(line), f)

                    if os.path.isdir(p):
                        p += "/"
                    ret.append(p)

    return ret


class InputPopup(Popup):
    def __init__(self,parent_mode,title,width_req=-1,height_req=-1,close_cb=None):
        Popup.__init__(self,parent_mode,title,width_req,height_req,close_cb)
        self.input_list = []
        self.input_states = {}
        self.current_input = 0
        self.tab_count = 0
        self.opts = None
        self.opt_off = 0
        curses.curs_set(2)

    def add_text_input(self, message, name, value="", complete=True):
        """ 
        Add a text input field to the popup.
        
        :param message: string to display above the input field
        :param name: name of the field, for the return callback
        :param value: initial value of the field
        :param complete: should completion be run when tab is hit and this field is active
        """
        self.input_list.append(name)
        self.input_states[name] = [message,value,0,complete]

    def _refresh_lines(self):
        crow = 1
        for i,ipt in enumerate(self.input_list):
            msg,txt,curs,comp = self.input_states[ipt]
            if i == self.current_input:
                curs_row = crow+1
                curs_col = curs
                if self.opts:
                    self.parent.add_string(crow+2,self.opts[self.opt_off:],self.screen,1,False,True)
            self.parent.add_string(crow,msg,self.screen,1,False,True)
            self.parent.add_string(crow+1,"{!selected!}%s"%txt.ljust(self.width-2),self.screen,1,False,False)
            crow += 3

        self.screen.move(curs_row,curs_col+1)

    def _get_current_input_value(self):
        return self.input_states[self.input_list[self.current_input]][1]

    def _set_current_input_value(self, val):
        self.input_states[self.input_list[self.current_input]][1] = val

    def _get_current_cursor(self):
        return self.input_states[self.input_list[self.current_input]][2]

    def _move_current_cursor(self, amt):
        self.input_states[self.input_list[self.current_input]][2] += amt

    def _set_current_cursor(self, pos):
        self.input_states[self.input_list[self.current_input]][2] = pos

    # most of the cursor,input stuff here taken from ui/console/screen.py
    def handle_read(self, c):
        if c == curses.KEY_UP:
            self.current_input = max(0,self.current_input-1)
        elif c == curses.KEY_DOWN:
            self.current_input = min(len(self.input_list)-1,self.current_input+1)

        elif c == curses.KEY_ENTER or c == 10:
            if self._close_cb:
                vals = {}
                for ipt in self.input_list:
                    vals[ipt] = self.input_states[ipt][1]
                curses.curs_set(0)
                self._close_cb(vals)
            return True # close the popup

        elif c == 9:
            # Keep track of tab hit count to know when it's double-hit
            self.tab_count += 1
            if self.tab_count > 1:
                second_hit = True
                self.tab_count = 0
            else:
                second_hit = False

            # We only call the tab completer function if we're at the end of
            # the input string on the cursor is on a space
            cur_input = self._get_current_input_value()
            cur_cursor = self._get_current_cursor()
            if cur_cursor == len(cur_input) or cur_input[cur_cursor] == " ":
                if self.opts:
                    prev = self.opt_off
                    self.opt_off += self.width-3
                    # now find previous double space, best guess at a split point
                    # in future could keep opts unjoined to get this really right
                    self.opt_off = self.opts.rfind("  ",0,self.opt_off)+2
                    if second_hit and self.opt_off == prev: # double tap and we're at the end
                        self.opt_off = 0
                else:
                    opts = complete(cur_input)
                    if len(opts) == 1: # only one option, just complete it
                        self._set_current_input_value(opts[0])
                        self._set_current_cursor(len(opts[0]))
                        self.tab_count = 0
                    elif len(opts) > 1 and second_hit: # display multiple options on second tab hit
                        self.opts = "  ".join(opts)

        elif c == 27: # close on esc, no action
            return True

        # Cursor movement
        elif c == curses.KEY_LEFT:
            if self._get_current_cursor():
                self._move_current_cursor(-1)
        elif c == curses.KEY_RIGHT:
            if self._get_current_cursor() < len(self._get_current_input_value()):
                self._move_current_cursor(1)
        elif c == curses.KEY_HOME:
            self._set_current_cursor(0)
        elif c == curses.KEY_END:
            self._set_current_cursor(len(self._get_current_input_value()))

        if c != 9:
            self.opts = None
            self.opt_off = 0
            self.tab_count = 0

        # Delete a character in the input string based on cursor position
        if c == curses.KEY_BACKSPACE or c == 127:
            cur_input = self._get_current_input_value()
            cur_cursor = self._get_current_cursor()
            if cur_input and  cur_cursor > 0:
                self._set_current_input_value(cur_input[:cur_cursor - 1] + cur_input[cur_cursor:])
                self._move_current_cursor(-1)
        elif c == curses.KEY_DC:
            cur_input = self._get_current_input_value()
            cur_cursor = self._get_current_cursor()
            if cur_input and cur_cursor < len(cur_input):
                self._set_current_input_value(cur_input[:cur_cursor] + cur_input[cur_cursor+1:])
        elif c > 31 and c < 256:
            cur_input = self._get_current_input_value()
            cur_cursor = self._get_current_cursor()
            # Emulate getwch
            stroke = chr(c)
            uchar = ""
            while not uchar:
                try:
                    uchar = stroke.decode(self.parent.encoding)
                except UnicodeDecodeError:
                    c = self.parent.stdscr.getch()
                    stroke += chr(c)
            if uchar:
                if cur_cursor == len(cur_input):
                    self._set_current_input_value(cur_input+uchar)
                else:
                    # Insert into string
                    self._set_current_input_value(cur_input[:cur_cursor] + uchar + cur_input[cur_cursor:])
                # Move the cursor forward
                self._move_current_cursor(1)

        self.refresh()
        return False

