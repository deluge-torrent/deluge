import gtk
import math

class PiecesTabManager(object):
    def __init__(self, manager):
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
        self.all_files = None
        self.file_priorities = None
        self.index = 0
        self.prev_file_index = -1
        self.file_index = 0
        self.next_file_index = 1
        self.num_files = 0
        self.current_first_index = None
        self.current_last_index = None

    def set_unique_id(self, unique_id):
        self.unique_id = unique_id

    def clear_pieces_store(self):
        self.unique_id = -1
        self.rows = 0
        self.peer_speed = []
        self.eventboxes = []
        self.progress = []
        self.piece_info = []
        self.tooltips = []
        self.all_files = None
        self.file_priorities = None
        self.current_first_index = None
        self.current_last_index = None
        self.index = 0
        self.num_files = 0
        self.prev_file_index = -1
        self.file_index = 0
        self.next_file_index = 1
        if not self.vbox is None:
            self.vbox.destroy()
        self.vbox = None
        
    def prepare_pieces_store(self):
        gtk.main_iteration_do(False)
        viewport = gtk.Viewport()
        scrolledWindow = gtk.ScrolledWindow()
        scrolledWindow.add(viewport)
        scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vbox = gtk.VBox()
        viewport.add(self.vbox)
        self.all_files = self.manager.get_file_piece_range(self.unique_id)
        self.file_priorities = self.manager.get_priorities(self.unique_id)
        state = self.manager.get_torrent_state(self.unique_id)
        self.num_pieces = state["num_pieces"]
        for priority in self.file_priorities:
            self.current_first_index = self.all_files[self.file_index]['first_index']
            self.current_last_index = self.all_files[self.file_index]['last_index']
            if priority > 0:
            #if file is being downloaded build the file pieces information
                self.build_file_pieces()
            else:
            #if file is not being downloaded skip the file pieces
                self.skip_current_file()
            self.file_index += 1
            self.next_file_index += 1
            self.prev_file_index += 1
        
        self.get_current_pieces_info()
        return scrolledWindow

    def build_file_pieces(self):
        gtk.main_iteration_do(False)
        label = gtk.Label()
        label.set_alignment(0,0)
        label.set_text(self.all_files[self.file_index]['path'])
        self.vbox.pack_start(label, expand=False)
        table = gtk.Table()
        self.rows = int(math.ceil((self.current_last_index-self.current_first_index)/self.columns)+1)
        self.vbox.pack_start(table, expand=False)
        table.resize(self.rows, self.columns)
        table.set_size_request((self.columns+1)*self.piece_width, (self.rows+1)*self.piece_height)
        if self.current_last_index != self.current_first_index:
        #if there is more than one piece
            self.build_pieces_table(table)
            only_one_piece = False
        else:
        #if file only has one piece
            self.index = 0
            only_one_piece = True
        self.piece_info.append({'blocks_total':0, 'blocks_finished':0, 'blocks_requested':0})
        self.progress.append(gtk.ProgressBar())
        self.tooltips.append(gtk.Tooltips())
        self.eventboxes.append(gtk.EventBox())
        self.peer_speed.append("unknown")
        main_index = self.current_last_index
        if self.file_index > 0 and not self.piece_info[main_index] is None and only_one_piece:
        #if file has only one piece and it is shared destroy the table
            table.destroy()
        if self.file_index == 0 or self.piece_info[main_index] is None or not only_one_piece:
        # piece could be shared if file has only one piece and it's not the first file
        # only create it if it does not exist
            self.build_last_file_piece(table, main_index, only_one_piece)

    def build_pieces_table(self, table):
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
        temp_first_index = self.current_first_index
        for index in xrange(temp_range):
            gtk.main_iteration_do(False)
            main_index = diff+temp_first_index+index
            if temp_prev_priority > 0:
            #normal behavior
                self.piece_info.append({'blocks_total':0, 'blocks_finished':0, 'blocks_requested':0})
                self.progress.append(gtk.ProgressBar())
                self.tooltips.append(gtk.Tooltips())
                self.eventboxes.append(gtk.EventBox())
                self.peer_speed.append("unknown")
            else:
            #if first piece is shared with a skipped file
                self.share_skipped_piece(main_index)
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
        self.index = temp_range

    def build_last_file_piece(self, table, main_index, only_one_piece):
        gtk.main_iteration_do(False)
        if only_one_piece and self.file_index > 0:
        #if piece is shared with a skipped file
            self.share_skipped_piece(main_index)
        self.progress[main_index].set_size_request(self.piece_width, self.piece_height)
        if self.next_file_index < len(self.all_files):
        # if there is another file
            if self.file_priorities[self.next_file_index]==0\
                or self.current_last_index != self.all_files[self.next_file_index]['first_index']:
            #if next file is skipped or there is no shared piece, keep last piece
                row=self.index/self.columns
                column=self.index%self.columns
                table.attach(self.eventboxes[main_index], column, column+1, row, row+1, 
                    xoptions=0, yoptions=0, xpadding=0, ypadding=0)
                self.eventboxes[main_index].add(self.progress[main_index])
            if self.file_priorities[self.next_file_index]>0\
                and self.current_last_index == self.all_files[self.next_file_index]['first_index']:
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
            row=self.index/self.columns
            column=self.index%self.columns
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

    def share_skipped_piece(self, main_index):
        self.piece_info[main_index] = {'blocks_total':0, 'blocks_finished':0, 'blocks_requested':0}
        self.progress[main_index] = gtk.ProgressBar()
        self.tooltips[main_index] = gtk.Tooltips()
        self.eventboxes[main_index] = gtk.EventBox()
        self.peer_speed[main_index] = "unknown"

    def skip_current_file(self):
        if self.file_index == 0\
            or self.current_first_index !=\
                self.all_files[self.prev_file_index]['last_index']:
        #if first piece is not shared
            temp_range = 1+self.current_last_index-self.current_first_index
        else:
        #if first piece is shared
            temp_range = self.current_last_index-self.current_first_index
        for index in xrange(temp_range):
            self.piece_info.append(None)
            self.progress.append(None)
            self.eventboxes.append(None)
            self.tooltips.append(None)
            self.peer_speed.append(None)

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

    def get_current_pieces_info(self):
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
