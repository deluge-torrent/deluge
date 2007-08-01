import gtk

class LogManager(object):
    def __init__(self, viewport, manager):
        self.viewport = viewport
        self.vbox = None
        self.manager = manager

    def clear_log_store(self):
        if not self.vbox is None:
            self.vbox.destroy()
        self.vbox = None
        
    def prepare_log_store(self):
        self.vbox = gtk.VBox()
        self.viewport.add(self.vbox)
        self.vbox.show_all()
    
    def handle_event(self, event):
        event_message = None
        if event['event_type'] is self.manager.constants['EVENT_FINISHED']:
            event_message = _("Torrent finished") + " {"+ _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + "}"
        if event['event_type'] is self.manager.constants['EVENT_PEER_ERROR']:
            event_message = _("Peer message") + " {" + _("event message: ") + event['message'] + ", " + _("ip address: ")\
                + event['ip'] + ", " + _("client: ") + event['client_ID'] + "}"
        if event['event_type'] is self.manager.constants['EVENT_INVALID_REQUEST']:
            event_message = _("Invalid request") + " {" + _("event message: ") + event['message'] + ", " + _("client: ")\
                + event['client_ID'] + "}"
        if event['event_type'] is self.manager.constants['EVENT_FILE_ERROR']:
            event_message = _("File error") + " {" + _("event message: ") + event['message'] + ", " + _("torrent: ")\
                + self.manager.unique_IDs[event['unique_ID']].filename + "}"
        if event['event_type'] is self.manager.constants['EVENT_HASH_FAILED_ERROR']:
            event_message = _("Hash failed error") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + ", "\
                + _("piece index: ") + str(event['piece_index']) + "}"
        if event['event_type'] is self.manager.constants['EVENT_PEER_BAN_ERROR']:
            event_message = _("Peer ban error") + " {" + _("event message: ") + event['message'] + ", " + _("ip address: ")\
                + event['ip'] + ", " + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + "}"
        if event['event_type'] is self.manager.constants['EVENT_FASTRESUME_REJECTED_ERROR']:
            event_message = _("Fastresume rejected error") + event['message'] + ", "\
                + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + "}"
        if event['event_type'] is self.manager.constants['EVENT_TRACKER_ANNOUNCE']:
            event_message = _("Tracker announce") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + "}"
        if event['event_type'] is self.manager.constants['EVENT_TRACKER_REPLY']:
            event_message = _("Tracker reply") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + "}"
        if event['event_type'] is self.manager.constants['EVENT_TRACKER_ALERT']:
            event_message = _("Tracker alert") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + ", "\
                + _("status code: ") + str(event['status_code']) + ", " + _("Times in a row: ")\
                + str(event['times_in_row']) + "}"
        if event['event_type'] is self.manager.constants['EVENT_TRACKER_WARNING']:
            event_message = _("Tracker warning") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + "}"
        if event['event_type'] is self.manager.constants['EVENT_STORAGE_MOVED']:
            event_message = _("Storage moved") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + "}"
        if event['event_type'] is self.manager.constants['EVENT_PIECE_FINISHED']:
            event_message = _("Piece finished") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + ", "\
                + _("piece index: ") + str(event['piece_index']) + "}"
        if event['event_type'] is self.manager.constants['EVENT_BLOCK_DOWNLOADING']:
            event_message = _("Block downloading") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + ", "\
                + _("piece index: ") + str(event['piece_index']) + ", " + _("block index: ")\
                + str(event['block_index']) + ", " + _("peer speed: ") + event['peer_speed'] + "}"
        if event['event_type'] is self.manager.constants['EVENT_BLOCK_FINISHED']:
            event_message = _("Block finished") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + self.manager.unique_IDs[event['unique_ID']].filename + ", "\
                + _("piece index: ") + str(event['piece_index']) + ", " + _("block index: ")\
                + str(event['block_index']) + "}"
        if event['event_type'] is self.manager.constants['EVENT_OTHER']:
            event_message = _("Other") + " {" + _("event message: ") + event['message'] + "}"
        if not event_message is None:
            label = gtk.Label()
            label.set_text(event_message)
            label.set_alignment(0,0)
            label.set_selectable(True)
            self.vbox.pack_start(label, expand=False)
            label.show()
