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

class InputField:
    depend = None
    # render the input.  return number of rows taken up
    def render(self,screen,row,width,selected,col=1):
        return 0
    def handle_read(self, c):
        if c in [curses.KEY_ENTER, 10, 127, 113]:
            return True
        return False
    def get_value(self):
        return None
    def set_value(self, value):
        pass

    def set_depend(self,i,inverse=False):
        if not isinstance(i,CheckedInput):
            raise Exception("Can only depend on CheckedInputs")
        self.depend = i
        self.inverse = inverse

    def depend_skip(self):
        if not self.depend:
            return False
        if self.inverse:
            return self.depend.checked
        else:
            return not self.depend.checked

class CheckedInput(InputField):
    def __init__(self, parent, message, name, checked=False):
        self.parent = parent
        self.chkd_inact = "[X] %s"%message
        self.unchkd_inact = "[ ] %s"%message
        self.chkd_act = "[{!black,white,bold!}X{!white,black!}] %s"%message
        self.unchkd_act = "[{!black,white,bold!} {!white,black!}] %s"%message
        self.name = name
        self.checked = checked

    def render(self, screen, row, width, active, col=1):
        if self.checked and active:
            self.parent.add_string(row,self.chkd_act,screen,col,False,True)
        elif self.checked:
            self.parent.add_string(row,self.chkd_inact,screen,col,False,True)
        elif active:
            self.parent.add_string(row,self.unchkd_act,screen,col,False,True)
        else:
            self.parent.add_string(row,self.unchkd_inact,screen,col,False,True)
        return 1
        
    def handle_read(self, c):
        if c == 32:
            self.checked = not self.checked

    def get_value(self):
        return self.checked

    def set_value(self, c):
        self.checked = c


class CheckedPlusInput(InputField):
    def __init__(self, parent, message, name, child,checked=False):
        self.parent = parent
        self.chkd_inact = "[X] %s"%message
        self.unchkd_inact = "[ ] %s"%message
        self.chkd_act = "[{!black,white,bold!}X{!white,black!}] %s"%message
        self.unchkd_act = "[{!black,white,bold!} {!white,black!}] %s"%message
        self.name = name
        self.checked = checked
        self.msglen = len(self.chkd_inact)+1
        self.child = child
        self.child_active = False

    def render(self, screen, row, width, active, col=1):
        isact = active and not self.child_active
        if self.checked and isact:
            self.parent.add_string(row,self.chkd_act,screen,col,False,True)
        elif self.checked:
            self.parent.add_string(row,self.chkd_inact,screen,col,False,True)
        elif isact:
            self.parent.add_string(row,self.unchkd_act,screen,col,False,True)
        else:
            self.parent.add_string(row,self.unchkd_inact,screen,col,False,True)

        if active and self.checked and self.child_active:
            self.parent.add_string(row+1,"(esc to leave)",screen,col,False,True)
        elif active and self.checked:
            self.parent.add_string(row+1,"(right arrow to edit)",screen,col,False,True)
        rows = 2
        # show child
        if self.checked:
            if isinstance(self.child,(TextInput,IntSpinInput,FloatSpinInput)):
                crows = self.child.render(screen,row,width-self.msglen,self.child_active and active,col+self.msglen,self.msglen)
            else:
                crows = self.child.render(screen,row,width-self.msglen,self.child_active and active,col+self.msglen)
            rows = max(rows,crows)
        else:
            self.parent.add_string(row,"(enable to view/edit value)",screen,col+self.msglen,False,True)
        return rows
        
    def handle_read(self, c):
        if self.child_active:
            if c == 27: # leave child on esc
                self.child_active = False
                return
            # pass keys through to child
            self.child.handle_read(c)
        else:
            if c == 32:
                self.checked = not self.checked
            if c == curses.KEY_RIGHT:
                self.child_active = True

    def get_value(self):
        return self.checked

    def set_value(self, c):
        self.checked = c

    def get_child(self):
        return self.child



class IntSpinInput(InputField):
    def __init__(self, parent, message, name, move_func, value, min_val, max_val):
        self.parent = parent
        self.message = message
        self.name = name
        self.value = int(value)
        self.initvalue = self.value
        self.valstr = "%d"%self.value
        self.cursor = len(self.valstr)
        self.cursoff = len(self.message)+4 # + 4 for the " [ " in the rendered string
        self.move_func = move_func
        self.min_val = min_val
        self.max_val = max_val

    def render(self, screen, row, width, active, col=1, cursor_offset=0):
        if not active and not self.valstr:
            self.value = self.initvalue
            self.valstr = "%d"%self.value 
            self.cursor = len(self.valstr)
        if not self.valstr:
            self.parent.add_string(row,"%s [  ]"%self.message,screen,col,False,True)
        elif active:
            self.parent.add_string(row,"%s [ {!black,white,bold!}%d{!white,black!} ]"%(self.message,self.value),screen,col,False,True)
        else:
            self.parent.add_string(row,"%s [ %d ]"%(self.message,self.value),screen,col,False,True)

        if active:
            self.move_func(row,self.cursor+self.cursoff+cursor_offset)

        return 1

    def handle_read(self, c):
        if c  == curses.KEY_PPAGE:
            self.value+=1
        elif c == curses.KEY_NPAGE:
            self.value-=1
        elif c == curses.KEY_LEFT:
            self.cursor = max(0,self.cursor-1)
        elif c == curses.KEY_RIGHT:
            self.cursor = min(len(self.valstr),self.cursor+1)
        elif c == curses.KEY_HOME:
            self.cursor = 0
        elif c == curses.KEY_END:
            self.cursor = len(self.value)
        elif c == curses.KEY_BACKSPACE or c == 127:
            if self.valstr and  self.cursor > 0:
                self.valstr = self.valstr[:self.cursor - 1] + self.valstr[self.cursor:]
                self.cursor-=1
                if self.valstr:
                    self.value = int(self.valstr)
        elif c == curses.KEY_DC:
            if self.valstr and self.cursor < len(self.valstr):
                self.valstr = self.valstr[:self.cursor] + self.valstr[self.cursor+1:]
        elif c > 47 and c < 58:
            if c == 48 and self.cursor == 0: return
            if self.cursor == len(self.valstr):
                self.valstr += chr(c)
                self.value = int(self.valstr)
            else:
                # Insert into string
                self.valstr = self.valstr[:self.cursor] + chr(c) + self.valstr[self.cursor:]
                self.value = int(self.valstr)
            # Move the cursor forward
            self.cursor+=1
            

    def get_value(self):
        return self.value

    def set_value(self, val):
        self.value = int(val)
        self.valstr = "%d"%self.value
        self.cursor = len(self.valstr)


class FloatSpinInput(InputField):
    def __init__(self, parent, message, name, move_func, value, inc_amt, precision, min_val, max_val):
        self.parent = parent
        self.message = message
        self.name = name
        self.precision = precision
        self.inc_amt = inc_amt
        self.value = round(float(value),self.precision)
        self.initvalue = self.value
        self.fmt = "%%.%df"%precision
        self.valstr = self.fmt%self.value
        self.cursor = len(self.valstr)
        self.cursoff = len(self.message)+4 # + 4 for the " [ " in the rendered string
        self.move_func = move_func
        self.min_val = min_val
        self.max_val = max_val
        self.need_update = False

    def render(self, screen, row, width, active, col=1, cursor_offset=0):
        if not active and not self.valstr:
            self.value = self.initvalue
            self.valstr = self.fmt%self.value
            self.cursor = len(self.valstr)
        if not active and self.need_update:
            self.value = round(float(self.valstr),self.precision)
            self.valstr = self.fmt%self.value
            self.cursor = len(self.valstr)
        if not self.valstr:
            self.parent.add_string(row,"%s [  ]"%self.message,screen,col,False,True)
        elif active:
            self.parent.add_string(row,"%s [ {!black,white,bold!}%s{!white,black!} ]"%(self.message,self.valstr),screen,col,False,True)
        else:
            self.parent.add_string(row,"%s [ %s ]"%(self.message,self.valstr),screen,col,False,True)
        if active:
            self.move_func(row,self.cursor+self.cursoff+cursor_offset)

        return 1

    def handle_read(self, c):
        if c  == curses.KEY_PPAGE:
            self.value+=self.inc_amt
            self.valstr = self.fmt%self.value
            self.cursor = len(self.valstr)
        elif c == curses.KEY_NPAGE:
            self.value-=self.inc_amt
            self.valstr = self.fmt%self.value
            self.cursor = len(self.valstr)
        elif c == curses.KEY_LEFT:
            self.cursor = max(0,self.cursor-1)
        elif c == curses.KEY_RIGHT:
            self.cursor = min(len(self.valstr),self.cursor+1)
        elif c == curses.KEY_HOME:
            self.cursor = 0
        elif c == curses.KEY_END:
            self.cursor = len(self.value)
        elif c == curses.KEY_BACKSPACE or c == 127:
            if self.valstr and  self.cursor > 0:
                self.valstr = self.valstr[:self.cursor - 1] + self.valstr[self.cursor:]
                self.cursor-=1
                self.need_update = True
        elif c == curses.KEY_DC:
            if self.valstr and self.cursor < len(self.valstr):
                self.valstr = self.valstr[:self.cursor] + self.valstr[self.cursor+1:]
                self.need_update = True
        elif c == 45 and self.cursor == 0 and self.min_val < 0:
            minus_place = self.valstr.find('-')
            if minus_place >= 0: return
            self.valstr = chr(c)+self.valstr
            self.cursor += 1
            self.need_update = True
        elif c == 46:
            minus_place = self.valstr.find('-')
            if self.cursor <= minus_place: return
            point_place = self.valstr.find('.')
            if point_place >= 0: return
            if self.cursor == len(self.valstr):
                self.valstr += chr(c)
            else:
                # Insert into string
                self.valstr = self.valstr[:self.cursor] + chr(c) + self.valstr[self.cursor:]
            self.need_update = True
            # Move the cursor forward
            self.cursor+=1
        elif (c > 47 and c < 58):
            minus_place = self.valstr.find('-')
            if self.cursor <= minus_place: return
            if self.cursor == len(self.valstr):
                self.valstr += chr(c)
            else:
                # Insert into string
                self.valstr = self.valstr[:self.cursor] + chr(c) + self.valstr[self.cursor:]
            self.need_update = True
            # Move the cursor forward
            self.cursor+=1
            

    def get_value(self):
        return self.value

    def set_value(self, val):
        self.value = round(float(val),self.precision)
        self.valstr = self.fmt%self.value
        self.cursor = len(self.valstr)


class SelectInput(InputField):
    def __init__(self, parent, message, name, opts, vals, selidx):
        self.parent = parent
        self.message = message
        self.name = name
        self.opts = opts
        self.vals = vals
        self.selidx = selidx

    def render(self, screen, row, width, selected, col=1):
        if self.message:
            self.parent.add_string(row,self.message,screen,col,False,True)
            row += 1
        off = col+1
        for i,opt in enumerate(self.opts):
            if selected and i == self.selidx:
                self.parent.add_string(row,"{!black,white,bold!}[%s]"%opt,screen,off,False,True)
            elif i == self.selidx:
                self.parent.add_string(row,"[{!white,black,underline!}%s{!white,black!}]"%opt,screen,off,False,True)
            else:
                self.parent.add_string(row,"[%s]"%opt,screen,off,False,True)
            off += len(opt)+3
        if self.message:
            return 2
        else:
            return 1

    def handle_read(self, c):
        if c == curses.KEY_LEFT:
            self.selidx = max(0,self.selidx-1)
        if c == curses.KEY_RIGHT:
            self.selidx = min(len(self.opts)-1,self.selidx+1)

    def get_value(self):
        return self.vals[self.selidx]

    def set_value(self, nv):
        for i,val in enumerate(self.vals):
            if nv == val:
                self.selidx = i
                return
        raise Exception("Invalid value for SelectInput")

class TextInput(InputField):
    def __init__(self, parent, move_func, width, message, name, value, docmp):
        self.parent = parent
        self.move_func = move_func
        self.width = width

        self.message = message
        self.name = name
        self.value = value
        self.docmp = docmp

        self.tab_count = 0
        self.cursor = len(self.value)
        self.opts = None
        self.opt_off = 0

    def render(self,screen,row,width,selected,col=1,cursor_offset=0):
        if self.message:
            self.parent.add_string(row,self.message,screen,col,False,True)
            row += 1
        if selected:
            if self.opts:
                self.parent.add_string(row+1,self.opts[self.opt_off:],screen,col,False,True)
            if self.cursor > (width-3):
                self.move_func(row,width-2)
            else:
                self.move_func(row,self.cursor+1+cursor_offset)
        slen = len(self.value)+3
        if slen > width:
            vstr = self.value[(slen-width):]
        else:
            vstr = self.value.ljust(width-2)
        self.parent.add_string(row,"{!black,white,bold!}%s"%vstr,screen,col,False,False)

        if self.message:
            return 3
        else:
            return 2

    def get_value(self):
        return self.value

    def set_value(self,val):
        self.value = val
        self.cursor = len(self.value)

    # most of the cursor,input stuff here taken from ui/console/screen.py
    def handle_read(self,c):
        if c == 9 and self.docmp:
            # Keep track of tab hit count to know when it's double-hit
            self.tab_count += 1
            if self.tab_count > 1:
                second_hit = True
                self.tab_count = 0
            else:
                second_hit = False

            # We only call the tab completer function if we're at the end of
            # the input string on the cursor is on a space
            if self.cursor == len(self.value) or self.value[self.cursor] == " ":
                if self.opts:
                    prev = self.opt_off
                    self.opt_off += self.width-3
                    # now find previous double space, best guess at a split point
                    # in future could keep opts unjoined to get this really right
                    self.opt_off = self.opts.rfind("  ",0,self.opt_off)+2
                    if second_hit and self.opt_off == prev: # double tap and we're at the end
                        self.opt_off = 0
                else:
                    opts = self.complete(self.value)
                    if len(opts) == 1: # only one option, just complete it
                        self.value = opts[0]
                        self.cursor = len(opts[0])
                        self.tab_count = 0
                    elif len(opts) > 1 and second_hit: # display multiple options on second tab hit
                        self.opts = "  ".join(opts)

        # Cursor movement
        elif c == curses.KEY_LEFT:
            self.cursor = max(0,self.cursor-1)
        elif c == curses.KEY_RIGHT:
            self.cursor = min(len(self.value),self.cursor+1)
        elif c == curses.KEY_HOME:
            self.cursor = 0
        elif c == curses.KEY_END:
            self.cursor = len(self.value)

        if c != 9:
            self.opts = None
            self.opt_off = 0
            self.tab_count = 0

        # Delete a character in the input string based on cursor position
        if c == curses.KEY_BACKSPACE or c == 127:
            if self.value and  self.cursor > 0:
                self.value = self.value[:self.cursor - 1] + self.value[self.cursor:]
                self.cursor-=1
        elif c == curses.KEY_DC:
            if self.value and self.cursor < len(self.value):
                self.value = self.value[:self.cursor] + self.value[self.cursor+1:]
        elif c > 31 and c < 256:
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
                if self.cursor == len(self.value):
                    self.value += uchar
                else:
                    # Insert into string
                    self.value = self.value[:self.cursor] + uchar + self.value[self.cursor:]
                # Move the cursor forward
                self.cursor+=1

    def complete(self,line):
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
        self.inputs = []
        self.current_input = 0

    def move(self,r,c):
        self._cursor_row = r
        self._cursor_col = c

    def add_text_input(self, message, name, value="", complete=True):
        """ 
        Add a text input field to the popup.
        
        :param message: string to display above the input field
        :param name: name of the field, for the return callback
        :param value: initial value of the field
        :param complete: should completion be run when tab is hit and this field is active
        """
        self.inputs.append(TextInput(self.parent, self.move, self.width, message,
                                     name, value, complete))

    def add_select_input(self, message, name, opts, vals, default_index=0):
        self.inputs.append(SelectInput(self.parent, message, name, opts, vals, default_index))

    def _refresh_lines(self):
        self._cursor_row = -1
        self._cursor_col = -1
        curses.curs_set(0)
        crow = 1
        for i,ipt in enumerate(self.inputs):
            crow += ipt.render(self.screen,crow,self.width,i==self.current_input)

        # need to do this last as adding things moves the cursor
        if self._cursor_row >= 0:
            curses.curs_set(2)
            self.screen.move(self._cursor_row,self._cursor_col)

    def handle_read(self, c):
        if c == curses.KEY_UP:
            self.current_input = max(0,self.current_input-1)
        elif c == curses.KEY_DOWN:
            self.current_input = min(len(self.inputs)-1,self.current_input+1)
        elif c == curses.KEY_ENTER or c == 10:
            if self._close_cb:
                vals = {}
                for ipt in self.inputs:
                    vals[ipt.name] = ipt.get_value()
                curses.curs_set(0)
                self._close_cb(vals)
            return True # close the popup
        elif c == 27: # close on esc, no action
            return True
        elif self.inputs:
            self.inputs[self.current_input].handle_read(c)

        self.refresh()
        return False

