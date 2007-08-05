import gtk
import xdg.BaseDirectory
import os
import time

CONFIG_DIR = xdg.BaseDirectory.save_config_path('deluge')

class LogTabManager(object):
    def __init__(self, viewport, manager):
        self.log_files = False
        self.viewport = viewport
        self.vbox = None
        self.manager = manager
        self.logdir = os.path.join(CONFIG_DIR, 'logs')
        if not os.path.isdir(self.logdir):
            os.mkdir(self.logdir)
        self.labels = []

    def clear_log_store(self):
        if not self.vbox is None:
            self.vbox.destroy()
        self.vbox = None
        
    def build_log_view(self):
        self.vbox = gtk.VBox()
        self.viewport.add(self.vbox)
        self.vbox.show_all()

    def enable_log_files(self):
        self.log_files = True

    def disable_log_files(self):
        self.log_files = False
    
    def handle_event(self, event):
        event_message = None
        if event['event_type'] is self.manager.constants['EVENT_FINISHED']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Torrent finished") + " {"+ _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + torrent + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_PEER_ERROR']:
            event_message = _("Peer message") + " {" + _("event message: ") + event['message'] + ", " + _("ip address: ")\
                + event['ip'] + ", " + _("client: ") + event['client_ID'] + "}"
            if self.log_files:
                log = os.path.join(self.logdir, 'peer_messages.log')
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_INVALID_REQUEST']:
            event_message = _("Invalid request") + " {" + _("event message: ") + event['message'] + ", " + _("client: ")\
                + event['client_ID'] + "}"
            if self.log_files:
                log = os.path.join(self.logdir, 'invalid_requests.log')
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_FILE_ERROR']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("File error") + " {" + _("event message: ") + event['message'] + ", " + _("torrent: ")\
                + torrent + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_HASH_FAILED_ERROR']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Hash failed error") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + torrent + ", "\
                + _("piece index: ") + str(event['piece_index']) + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_PEER_BAN_ERROR']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Peer ban error") + " {" + _("event message: ") + event['message'] + ", " + _("ip address: ")\
                + event['ip'] + ", " + _("torrent: ") + torrent + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_FASTRESUME_REJECTED_ERROR']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Fastresume rejected error") + event['message'] + ", "\
                + _("torrent: ") + torrent + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_TRACKER_ANNOUNCE']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Tracker announce") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + torrent + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_TRACKER_REPLY']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Tracker reply") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + torrent + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_TRACKER_ALERT']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Tracker alert") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + torrent + ", "\
                + _("status code: ") + str(event['status_code']) + ", " + _("Times in a row: ")\
                + str(event['times_in_row']) + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_TRACKER_WARNING']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Tracker warning") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + torrent + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_STORAGE_MOVED']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Storage moved") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + torrent + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_PIECE_FINISHED']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Piece finished") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + torrent + ", "\
                + _("piece index: ") + str(event['piece_index']) + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_BLOCK_DOWNLOADING']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Block downloading") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + torrent + ", "\
                + _("piece index: ") + str(event['piece_index']) + ", " + _("block index: ")\
                + str(event['block_index']) + ", " + _("peer speed: ") + event['peer_speed'] + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_BLOCK_FINISHED']:
            torrent = self.manager.unique_IDs[event['unique_ID']].filename.replace(os.path.join(CONFIG_DIR, 'torrentfiles/'), '')
            event_message = _("Block finished") + " {" + _("event message: ") + event['message'] + ", "\
                + _("torrent: ") + torrent + ", "\
                + _("piece index: ") + str(event['piece_index']) + ", " + _("block index: ")\
                + str(event['block_index']) + "}"
            if self.log_files:
                log = os.path.join(self.logdir, torrent.replace('.torrent', '.log'))
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if event['event_type'] is self.manager.constants['EVENT_OTHER']:
            event_message = _("Other") + " {" + _("event message: ") + event['message'] + "}"
            if self.log_files:
                log = os.path.join(self.logdir, 'other.log')
                logfile = open(log, "a")
                logfile.write(time.asctime(time.localtime()) + ", " +event_message + '\n')
                logfile.close()
        if not event_message is None:
            label = gtk.Label()
            self.labels.append(label)
            label.set_text(event_message)
            label.set_alignment(0,0)
            label.set_selectable(True)
            self.vbox.pack_end(label, expand=False)
            if len(self.labels)>100:
                remove_label = self.labels.pop(0)
                remove_label.destroy()
            label.show()
