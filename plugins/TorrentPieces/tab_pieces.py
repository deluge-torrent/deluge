from itertools import izip
import gtk
import math

class PiecesManager(object):
    def __init__(self, viewport, manager):
        self.viewport = viewport
        self.vbox = None
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
        self.first_indexes = []
        self.last_indexes = []

    def set_unique_id(self, unique_id):
        self.unique_id = unique_id

    def clear_pieces_store(self):
        self.unique_id = -1
        self.rows = 0
        if not self.vbox is None:
            self.vbox.destroy()
        self.vbox = None
        self.peer_speed = []
        self.eventboxes = []
        self.progress = []
        self.piece_info = []
        self.tooltips = []
        self.first_indexes = []
        self.last_indexes = []
        
    def prepare_pieces_store(self):
        self.vbox = gtk.VBox()
        self.viewport.add(self.vbox)
        all_files = self.manager.get_torrent_file_info(self.unique_id)
        file_priorities = self.manager.get_priorities(self.unique_id)
        state = self.manager.get_torrent_state(self.unique_id)
        num_pieces = state["num_pieces"]
        prev_file_index = -1
        file_index = 0
        next_file_index = 1
        for file, priority in izip(all_files, file_priorities):
            if file_index == 0:
                file_piece_range = self.manager.get_file_piece_range(self.unique_id,\
                    file_index, file['size'])
                self.first_indexes.append(file_piece_range['first_index'])
                self.last_indexes.append(file_piece_range['last_index'])
            if priority > 0:
            #if file is being downloaded build the file pieces information
                temp_prev_priority = 1
                label = gtk.Label()
                label.set_alignment(0,0)
                label.set_text(file['path'])
                self.vbox.pack_start(label, expand=False)
                table = gtk.Table()
                self.rows = int(math.ceil((self.last_indexes[file_index]-self.first_indexes[file_index])/self.columns)+1)
                self.vbox.pack_start(table, expand=False)
                table.resize(self.rows, self.columns)
                table.set_size_request((self.columns+1)*self.piece_width, (self.rows+1)*self.piece_height)
                index = None
                if self.last_indexes[file_index] != self.first_indexes[file_index]:
                #if there is more than one piece
                    if self.first_indexes[file_index] == 0\
                        or self.first_indexes[file_index] != self.last_indexes[prev_file_index]:
                    #if first piece is not a shared piece
                        temp_range = self.last_indexes[file_index]-self.first_indexes[file_index]
                        diff = 0
                    else:
                        #if first piece is shared
                        temp_prev_priority = file_priorities[prev_file_index]
                        if temp_prev_priority > 0:
                        #if last file was not skipped, skip the first piece
                            diff = 1
                            temp_range = self.last_indexes[file_index]-(self.first_indexes[file_index]+1)
                        #otherwise keep the first piece
                        else:
                            diff = 0
                            temp_range = self.last_indexes[file_index]-self.first_indexes[file_index]
                    #last piece handled outside of loop, skip it from range
                    for index in xrange(temp_range):
                        main_index = diff+self.first_indexes[file_index]+index
                        if temp_prev_priority > 0:
                        #normal behavior
                            self.piece_info.append({'blocks_total':0, 'blocks_finished':0, 'blocks_requested':0})
                            self.progress.append(gtk.ProgressBar())
                            self.tooltips.append(gtk.Tooltips())
                            self.eventboxes.append(gtk.EventBox())
                            self.peer_speed.append("unknown")
                        else:
                        #if first piece is shared with a skipped file
                            self.piece_info[main_index] = {'blocks_total':0, 'blocks_finished':0, 'blocks_requested':0}
                            self.progress[main_index] = gtk.ProgressBar()
                            self.tooltips[main_index] = gtk.Tooltips()
                            self.eventboxes[main_index] = gtk.EventBox()
                            self.peer_speed[main_index] = "unknown"
                            temp_prev_priority = 1
                        self.progress[main_index].set_size_request(self.piece_width, self.piece_height)
                        row = index/self.columns
                        column = index%self.columns
                        table.attach(self.eventboxes[main_index], column, column+1, row, row+1, 
                            xoptions=0, yoptions=0, xpadding=0, ypadding=0)
                        self.eventboxes[main_index].add(self.progress[main_index])
                        if self.manager.has_piece(self.unique_id, main_index):
                        #if piece is already finished
                            self.progress[main_index].set_fraction(1)
                            self.tooltips[main_index].set_tip(self.eventboxes[main_index], _("Piece finished"))
                        else:
                        #if piece is not already finished
                            self.tooltips[main_index].set_tip(self.eventboxes[main_index], _("Piece not started"))
                    self.piece_info.append({'blocks_total':0, 'blocks_finished':0, 'blocks_requested':0})
                    self.progress.append(gtk.ProgressBar())
                    self.tooltips.append(gtk.Tooltips())
                    self.eventboxes.append(gtk.EventBox())
                    self.peer_speed.append("unknown")
                    index = index+1
                    only_one_piece = False
                else:
                #if file only has one piece
                    index = 0
                    only_one_piece = True
                main_index = self.last_indexes[file_index]
                # do the following even if file has only one piece
                # and the piece does not need created
                if next_file_index < len(all_files):
                #if there is another file
                    file_piece_range = self.manager.get_file_piece_range(self.unique_id,\
                        next_file_index, file['size'])
                    self.first_indexes.append(file_piece_range['first_index'])
                    self.last_indexes.append(file_piece_range['last_index'])
                    if self.last_indexes[next_file_index] >= num_pieces:
                    #hack to fix libtorrent issue
                        self.last_indexes[next_file_index] = num_pieces-1
                if file_index > 0 and not self.piece_info[main_index] is None and only_one_piece:
                #if file has only one piece and it is shared destroy the table
                    table.destroy()
                if file_index == 0 or self.piece_info[main_index] is None or not only_one_piece:
                # piece could be shared if file has only one piece and it's not the first file
                # only create it if it does not exist
                    if only_one_piece:
                    #if piece is shared with a skipped file
                        self.piece_info[main_index] = {'blocks_total':0, 'blocks_finished':0, 'blocks_requested':0}
                        self.progress[main_index] = gtk.ProgressBar()
                        self.tooltips[main_index] = gtk.Tooltips()
                        self.eventboxes[main_index] = gtk.EventBox()
                        self.peer_speed[main_index] = "unknown"
                    self.progress[main_index].set_size_request(self.piece_width, self.piece_height)
                    if next_file_index < len(all_files):
                    # if there is another file
                        if file_priorities[next_file_index]==0\
                            or self.last_indexes[file_index] != self.first_indexes[next_file_index]:
                        #if next file is skipped or there is no shared piece, keep last piece
                            row=index/self.columns
                            column=index%self.columns
                            table.attach(self.eventboxes[main_index], column, column+1, row, row+1, 
                                xoptions=0, yoptions=0, xpadding=0, ypadding=0)
                            self.eventboxes[main_index].add(self.progress[main_index])
                        if file_priorities[next_file_index]>0\
                            and self.last_indexes[file_index] == self.first_indexes[next_file_index]:
                        #if next file is not skipped and there is a shared piece, do not keep last piece
                            if only_one_piece:
                            #only piece in file is shared, destroy table for file
                                table.destroy()
                            label = gtk.Label()
                            label.set_alignment(0,0)
                            label.set_text(_("Piece shared with next file(s)"))
                            self.vbox.pack_start(label, expand=False)
                            temp_table = gtk.Table()
                            temp_table.resize(1,2)
                            temp_table.set_size_request(self.piece_width, 2*self.piece_height)
                            temp_table.attach(self.eventboxes[main_index], 0, 1, 0, 1, 
                                xoptions=0, yoptions=0, xpadding=0, ypadding=0)
                            self.eventboxes[main_index].add(self.progress[main_index])
                            self.vbox.pack_start(temp_table, expand=False)
                    else:
                    #if there is no other file
                        row=index/self.columns
                        column=index%self.columns
                        table.attach(self.eventboxes[main_index], column, column+1, row, row+1, 
                            xoptions=0, yoptions=0, xpadding=0, ypadding=0)
                        self.eventboxes[main_index].add(self.progress[main_index])
                    if self.manager.has_piece(self.unique_id, main_index):
                    #if the last piece is already finished
                        self.progress[main_index].set_fraction(1)
                        self.tooltips[main_index].set_tip(self.eventboxes[main_index], _("Piece finished"))
                    else:
                    #if the last piece is not already finished
                        self.tooltips[main_index].set_tip(self.eventboxes[main_index], _("Piece not started"))
            else:
            #if file is not being downloaded skip the file pieces
                if self.first_indexes[file_index] == 0 or self.first_indexes[file_index] != self.last_indexes[prev_file_index]:
                #if first piece is not shared
                    temp_range = 1+self.last_indexes[file_index]-self.first_indexes[file_index]
                else:
                #if first piece is shared
                    temp_range = self.last_indexes[file_index]-self.first_indexes[file_index]
                for index in xrange(temp_range):
                    self.piece_info.append(None)
                    self.progress.append(None)
                    self.eventboxes.append(None)
                    self.tooltips.append(None)
                    self.peer_speed.append(None)
                if next_file_index < len(all_files):
                #if there is another file
                    file_piece_range = self.manager.get_file_piece_range(self.unique_id,\
                        next_file_index, file['size'])
                    self.first_indexes.append(file_piece_range['first_index'])
                    self.last_indexes.append(file_piece_range['last_index'])
                    if self.last_indexes[next_file_index] >= num_pieces:
                        self.last_indexes[next_file_index] = num_pieces-1
            file_index += 1
            next_file_index += 1
            prev_file_index += 1
        
        #get currently downloading piece information
        all_piece_info = self.manager.get_all_piece_info(self.unique_id)
        for piece_index in all_piece_info:
            index = piece_index['piece_index']
            if not self.piece_info[index] is None:
                temp_piece_info = {'blocks_total':piece_index['blocks_total'], \
                    'blocks_finished':piece_index['blocks_finished']}
                self.piece_info[index] = temp_piece_info
                blocks_total = str(temp_piece_info['blocks_total'])
                info_string = str(temp_piece_info['blocks_finished']) + "/" + blocks_total + " " + _("blocks finished") + "\n" \
                    + _("peer speed: unknown")
                if self.progress[index].get_fraction() == 0:
                    self.progress[index].set_fraction(0.5)
                    self.tooltips[index].set_tip(self.eventboxes[index], info_string)
        self.vbox.show_all()
    
    def handle_event(self, event):
        #protect against pieces trying to display after file priority changed
        #or different torrent selected
        if event['unique_ID'] == self.unique_id\
                and not self.piece_info[event['piece_index']] is None:
            if event['event_type'] is self.manager.constants['EVENT_PIECE_FINISHED']:
                self.update_pieces_store(event['piece_index'], piece_finished=True)
            elif event['event_type'] is self.manager.constants['EVENT_BLOCK_DOWNLOADING']:
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
