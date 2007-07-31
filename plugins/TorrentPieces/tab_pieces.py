import gtk

import math

class PiecesManager(object):
    def __init__(self, table, manager):
        self.table = table
        self.manager = manager
        self.progress = []
        self.tooltips = []
        self.eventboxes = []
        self.rows = 0
        self.columns = 33
        self.piece_width = 30
        self.piece_height = 20
        self.unique_id = -1
        self.peer_speed = []
        self.piece_info = []

    def set_unique_id(self, unique_id):
        self.unique_id = unique_id

    def clear_pieces_store(self):
        self.unique_id = -1
        self.rows = 0
        for widget in self.eventboxes:
            widget.destroy()
        for widget in self.progress:
            widget.hide()
            widget.destroy()
        self.peer_speed = []
        self.eventboxes = []
        self.progress = []
        self.piece_info = []
        self.tooltips = []
        
    def prepare_pieces_store(self):
        state = self.manager.get_torrent_state(self.unique_id)
        num_pieces = state["num_pieces"]
        self.rows = int(math.ceil(num_pieces/self.columns))
        self.table.resize(self.rows, self.columns)
        self.table.set_size_request((self.columns+1)*self.piece_width, (self.rows+1)*self.piece_height)
        for index in xrange(num_pieces):
            self.piece_info.append({'blocks_total':0, 'blocks_finished':0, 'blocks_requested':0})
            self.progress.append(gtk.ProgressBar())
            self.tooltips.append(gtk.Tooltips())
            self.eventboxes.append(gtk.EventBox())
            self.peer_speed.append("unknown")
            self.progress[index].set_size_request(self.piece_width, self.piece_height)
            row = index/self.columns
            column = index%self.columns
            self.table.attach(self.eventboxes[index], column, column+1, row, row+1, 
                xoptions=0, yoptions=0, xpadding=0, ypadding=0)
            self.eventboxes[index].add(self.progress[index])
            if self.manager.has_piece(self.unique_id, index):
                self.progress[index].set_fraction(1)
                self.tooltips[index].set_tip(self.eventboxes[index], _("Piece finished"))
            else:
                self.tooltips[index].set_tip(self.eventboxes[index], _("Piece not started"))
            self.eventboxes[index].show_all()
        all_piece_info = self.manager.get_all_piece_info(self.unique_id)
        for piece_index in all_piece_info:
            temp_piece_info = {'blocks_total':piece_index['blocks_total'], \
                'blocks_finished':piece_index['blocks_finished']}
            self.piece_info[piece_index['piece_index']] = temp_piece_info
            blocks_total = str(temp_piece_info['blocks_total'])
            info_string = str(temp_piece_info['blocks_finished']) + "/" + blocks_total + " " + _("blocks finished") + "\n" \
                + _("peer speed: unknown")
            if self.progress[index].get_fraction() == 0:
                self.progress[index].set_fraction(0.5)
                self.tooltips[index].set_tip(self.eventboxes[index], info_string)
    
    def handle_event(self, event):
        if event['event_type'] is self.manager.constants['EVENT_PIECE_FINISHED']:
            if event['unique_ID'] == self.unique_id:
                self.update_pieces_store(event['piece_index'], piece_finished=True)
        elif event['event_type'] is self.manager.constants['EVENT_BLOCK_DOWNLOADING']:
            if event['unique_ID'] == self.unique_id:
                index = event['piece_index']
                if self.piece_info[index]['blocks_total'] == 0:
                    self.piece_info[index] = self.manager.get_piece_info(self.unique_id, index)
                temp_peer_speed = event['peer_speed']
                if temp_peer_speed == "fast":
                    peer_speed_msg = _("fast")
                elif temp_peer_speed == "slow":
                    peer_speed_msg = _("slow")
                elif temp_peer_speed == "medium":
                    peer_speed_msg = _("medium")
                else:
                    peer_speed_msg = _("unknown")
                self.peer_speed[index] = peer_speed_msg
                self.update_pieces_store(index)
        else:
            if event['unique_ID'] == self.unique_id:
                index = event['piece_index']
                if self.piece_info[index]['blocks_total'] == 0:
                    self.piece_info[index] = self.manager.get_piece_info(self.unique_id, index)
                else:
                    self.piece_info[index]['blocks_finished'] += 1
                self.update_pieces_store(event['piece_index'])

    def update_pieces_store(self, index, piece_finished=False):
        if piece_finished:
            self.progress[index].set_fraction(1)
            self.tooltips[index].set_tip(self.eventboxes[index], _("Piece finished"))
        else:
            temp_fraction = self.progress[index].get_fraction()
            if temp_fraction == 0:
                self.progress[index].set_fraction(0.5)
            if temp_fraction != 1:
                temp_piece_info = self.piece_info[index]
                blocks_total = str(temp_piece_info['blocks_total'])
                info_string = str(temp_piece_info['blocks_finished']) + "/" + blocks_total + " " + _("blocks finished") + "\n" \
                    + _("peer speed: ") + self.peer_speed[index]
                self.tooltips[index].set_tip(self.eventboxes[index], info_string)
