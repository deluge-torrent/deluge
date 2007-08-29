# -*- coding: utf-8 -*-
#
# tab_pieces.py
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

import gtk
import math

class PiecesTabManager(object):
    def __init__(self, manager, viewport, columns, font_size):
        self.manager = manager
        self.viewport = viewport
        self.font_desc = None
        self.set_font_size(font_size)
        self.columns = columns
        self.vbox = None
        self.pieces = {}
        self.labels = []
        self.rows = []
        self.pieces_block_info = {}
        self.speed_symbols = {}
        self.num_blocks = 0
        self.last_num_blocks = 0
        self.row = -1
        self.unique_id = -1
        self.all_files = None
        self.file_priorities = None
        self.index = 0
        self.prev_file_index = -1
        self.file_index = 0
        self.next_file_index = 1
        self.num_files = 0
        self.current_first_index = None
        self.current_last_index = None
        self.handlers_connected = False

    def set_unique_id(self, unique_id):
        self.unique_id = unique_id

    def clear_pieces_store(self, clear_unique_id=True):
        self.pieces = {}
        self.pieces_block_info = {}
        self.speed_symbols = {}
        self.labels = []
        self.rows = []
        self.row = -1
        if clear_unique_id:
            self.unique_id = -1
        self.all_files = None
        self.file_priorities = None
        self.index = 0
        self.prev_file_index = -1
        self.file_index = 0
        self.next_file_index = 1
        self.num_files = 0
        self.current_first_index = None
        self.current_last_index = None
        if not self.vbox is None:
            self.vbox.destroy()
        self.vbox = None
        
    def set_columns(self, columns):
        self.columns = columns

    def set_font_size(self, font_size):
        import pango
        self.font_desc = pango.FontDescription('monospace %s' % font_size)

    def prepare_pieces_store(self):
        gtk.main_iteration_do(False)
        self.vbox = gtk.VBox()
        self.viewport.add(self.vbox)
        torrent_state = self.manager.get_torrent_state(self.unique_id)
        if torrent_state['is_seed']:
            label = gtk.Label(_("Torrent complete"))
            label.set_alignment(0,0)
            self.vbox.pack_start(label, expand=False)
            self.vbox.show_all()
            return
        self.all_files = self.manager.get_file_piece_range(self.unique_id)
        self.num_blocks = self.all_files[0]['first_num_blocks']
        self.last_num_blocks = self.all_files[len(self.all_files)-1]['last_num_blocks']
        self.file_priorities = self.manager.get_priorities(self.unique_id)
        state = self.manager.get_torrent_state(self.unique_id)
        self.num_pieces = state["num_pieces"]
        for priority in self.file_priorities:
            try:
                self.current_first_index = self.all_files[self.file_index]['first_index']
                self.current_last_index = self.all_files[self.file_index]['last_index']
            except:
                print "length of all_files", len(self.all_files)
                print "length of file_priorities", len(self.file_priorities)
                print "file index", self.file_index
            else:
                if priority > 0:
                #if file is being downloaded build the file pieces information
                    self.build_file_pieces()
                self.file_index += 1
                self.next_file_index += 1
                self.prev_file_index += 1
        self.get_current_pieces_info()
        self.vbox.show_all()
        return

    def build_file_pieces(self):
        gtk.main_iteration_do(False)
        label = gtk.Label()
        label.set_alignment(0,0)
        label.set_text(self.all_files[self.file_index]['path'])
        self.vbox.pack_start(label, expand=False)
        if self.current_last_index != self.current_first_index:
        #if there is more than one piece
            self.build_pieces_table()
            self.vbox.pack_start(gtk.Label(), expand=False)
        else:
        #if file only has one piece
            self.index = 0
        main_index = self.current_last_index
        if self.file_index == 0 or not main_index in self.pieces:
        # piece could be shared if file has only one piece and it's not the first file
        # only create it if it does not exist
            self.build_last_file_piece(main_index)

    def build_pieces_table(self):
        temp_prev_priority = 1
        if self.file_index == 0\
            or self.current_first_index !=\
                self.all_files[self.prev_file_index]['last_index']:
        #if first piece is not a shared piece
            temp_range = self.current_last_index-self.current_first_index
            diff = 0
        else:
        #if first piece is shared
            temp_prev_priority = self.file_priorities[self.prev_file_index]
            if temp_prev_priority > 0:
            #if last file was not skipped, skip the first piece
                diff = 1
                temp_range = self.current_last_index-(self.current_first_index+1)
            #otherwise keep the first piece
            else:
                diff = 0
                temp_range = self.current_last_index-self.current_first_index
        #last piece handled outside of loop, skip it from range
        row_prev = 0
        for index in xrange(temp_range):
            gtk.main_iteration_do(False)
            main_index = diff+self.current_first_index+index
            row = index/self.columns
            column = index%self.columns
            if row == 0 and column == 0:
                self.row += 1
                self.rows.append([])
                self.labels.append(gtk.Label())
                self.labels[self.row].set_alignment(0,0)
                self.vbox.pack_start(self.labels[self.row], expand=False)
            if row > row_prev:
                self.row += 1
                row_list = {}
                self.rows.append([])
                self.labels.append(gtk.Label())
                self.labels[self.row].set_alignment(0,0)
                self.vbox.pack_start(self.labels[self.row], expand=False)
            percentage = "    0%  "
            self.pieces[main_index] = {'row':self.row, 'column':column}
            self.pieces_block_info[main_index] = 0
            self.speed_symbols[main_index] = " "
            row_prev = row
            if self.manager.has_piece(self.unique_id, main_index):
            #if piece is already finished
                percentage = "  100%  "
                self.pieces_block_info[main_index] = self.num_blocks
            self.rows[self.row].append(percentage)
            self.labels[self.row].modify_font(self.font_desc)
            self.labels[self.row].set_text(str(self.rows[self.row]))
        self.labels[self.row].set_alignment(0,0)
        self.index = temp_range

    def build_last_file_piece(self, main_index):
        gtk.main_iteration_do(False)
        if self.next_file_index < len(self.all_files):
        # if there is another file
            if self.file_priorities[self.next_file_index]==0\
                or self.current_last_index != self.all_files[self.next_file_index]['first_index']:
            #if next file is skipped or there is no shared piece, keep last piece
                row = self.index/self.columns
                column = self.index%self.columns
                if column == 0:
                    self.row += 1
                    self.labels.append(gtk.Label())
                    self.vbox.pack_start(self.labels[self.row], expand=False)
                    self.rows.append([])
                self.pieces[main_index] = {'row':self.row, 'column':column}
            if self.file_priorities[self.next_file_index]>0\
                and self.current_last_index == self.all_files[self.next_file_index]['first_index']:
            #if next file is not skipped and there is a shared piece, do not keep last piece
                self.row += 1
                label = gtk.Label()
                label.set_alignment(0,0)
                label.set_text(_("Piece shared with next file(s)"))
                self.vbox.pack_start(label, expand=False)
                self.labels.append(gtk.Label())
                self.vbox.pack_start(self.labels[self.row], expand=False)
                self.vbox.pack_start(gtk.Label(), expand=False)
                self.rows.append([])
                self.pieces[main_index] = {'row':self.row, 'column':0}
        else:
        #if there is no other file
            row = self.index/self.columns
            column = self.index%self.columns
            if column == 0:
                self.row += 1
                self.labels.append(gtk.Label())
                self.rows.append([])
            self.pieces[main_index] = {'row':self.row, 'column':column}
        percentage = "    0%  "
        self.pieces_block_info[main_index] = 0
        self.speed_symbols[main_index] = " "
        if self.manager.has_piece(self.unique_id, main_index):
        #if piece is already finished
            percentage = "  100%  "
        self.pieces_block_info[main_index] = self.num_blocks
        self.rows[self.row].append(percentage)
        self.labels[self.row].modify_font(self.font_desc)
        self.labels[self.row].set_text(str(self.rows[self.row]))
        self.labels[self.row].set_alignment(0,0)

    def connect_handlers(self):
        self.handlers_connected = True
        self.manager.connect_event(self.manager.constants['EVENT_PIECE_FINISHED'], self.handle_event)
        self.manager.connect_event(self.manager.constants['EVENT_BLOCK_FINISHED'], self.handle_event)
        self.manager.connect_event(self.manager.constants['EVENT_BLOCK_DOWNLOADING'], self.handle_event)
        self.manager.connect_event(self.manager.constants['EVENT_HASH_FAILED_ERROR'], self.handle_event)

    def disconnect_handlers(self):
        if self.handlers_connected:
            self.manager.disconnect_event(self.manager.constants['EVENT_PIECE_FINISHED'], self.handle_event)
            self.manager.disconnect_event(self.manager.constants['EVENT_BLOCK_FINISHED'], self.handle_event)
            self.manager.disconnect_event(self.manager.constants['EVENT_BLOCK_DOWNLOADING'], self.handle_event)
            self.manager.disconnect_event(self.manager.constants['EVENT_HASH_FAILED_ERROR'], self.handle_event)
            self.handlers_connected = False

    def handle_event(self, event):
        #protect against pieces trying to display after file priority changed
        #or different torrent selected
        if event['unique_ID'] == self.unique_id\
                and event['piece_index'] in self.pieces:
            index = event['piece_index']
            row = self.pieces[index]['row']
            column = self.pieces[index]['column']
            if event['event_type'] is self.manager.constants['EVENT_PIECE_FINISHED']:
                self.rows[row][column] = "  100%  "
                if index == self.all_files[len(self.all_files)-1]['last_index']:
                    self.pieces_block_info[index] = self.last_num_blocks
                else:
                    self.pieces_block_info[index] = self.num_blocks
                self.labels[row].set_text(str(self.rows[row]))
            elif event['event_type'] is self.manager.constants['EVENT_HASH_FAILED_ERROR']:
                self.rows[row][column] = "    0%  "
                self.pieces_block_info[index] = 0
            elif event['event_type'] is self.manager.constants['EVENT_BLOCK_DOWNLOADING']:
                if index == self.all_files[len(self.all_files)-1]['last_index']:
                    percentage = (100*self.pieces_block_info[index])/self.last_num_blocks
                else:
                    percentage = (100*self.pieces_block_info[index])/self.num_blocks
                # Pad accordingly
                symbol = " "
                if event['peer_speed'] == "fast":
                    symbol = "+"
                elif event['peer_speed'] == "medium":
                    symbol = "="
                elif event['peer_speed'] == "slow":
                    symbol = "-"
                percentage_label = " "
                if percentage < 99:
                    if percentage <= 9:
                        percentage_label = "   "
                    else:
                        percentage_label = "  "
                self.speed_symbols[index] = symbol
                percentage_label = symbol + percentage_label + str(percentage) + "%  "
                self.rows[row][column] = percentage_label
                self.labels[row].set_text(str(self.rows[row]))
            else: # block finished
                self.pieces_block_info[index] += 1
                if index == self.all_files[len(self.all_files)-1]['last_index']:
                    percentage = (100*self.pieces_block_info[index])/self.last_num_blocks
                else:
                    percentage = (100*self.pieces_block_info[index])/self.num_blocks
                # Pad accordingly
                percentage_label = " "
                if percentage < 99:
                    if percentage <= 9:
                        percentage_label = "   "
                    else:
                        percentage_label = "  "
                percentage_label = self.speed_symbols[index] + percentage_label + str(percentage) + "%  "
                self.rows[row][column] = percentage_label
                self.labels[row].set_text(str(self.rows[row]))

    def get_current_pieces_info(self):
        all_piece_info = self.manager.get_all_piece_info(self.unique_id)
        for info_index in xrange(len(all_piece_info)):
            index = all_piece_info[info_index]['piece_index']
            if index in self.pieces:
                row = self.pieces[index]['row']
                column = self.pieces[index]['column']
                if index == self.all_files[len(self.all_files)-1]['last_index']:
                    percentage = (100*self.pieces_block_info[index])/self.last_num_blocks
                else:
                    percentage = (100*self.pieces_block_info[index])/self.num_blocks
                # Pad accordingly
                label = "  "
                if percentage < 99:
                    if percentage <= 9:
                        label = "    "
                    else:
                        label = "  "
                label = label + str(percentage) + "%  "
                self.rows[row][column] = label
                self.labels[row].set_text(str(self.rows[row]))

