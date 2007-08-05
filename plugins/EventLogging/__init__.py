# Copyright (C) 2007 - Micah Bucy <eternalsword@gmail.com>
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

### Initialization ###

plugin_name = _("Event Logging")
plugin_author = "Micah Bucy"
plugin_version = "0.2"
plugin_description = _("""
Adds a tab with log of selected events.

Event messages come from libtorrent alerts.
If you want those strings translated to your locale,
you'll have to report the issue with libtorrent, not deluge.

Regarding the log files, the logs are saved in a log
directory within the deluge config directory.  Event
messages for specific torrents are saved to individual
log files named the same as the associated .torrent
file.  Event messages not specific to any torrent are
saved to logs named after the events
(eg peer_messages.log).
Event messages in the log files also include a timestamp.
The user is responsible to cleanout the logs.

As of v0.2
Events are now truncated in display.  Log files are not.
New events are now displayed at the top.
""")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return EventLogging(path, core, interface)

### The Plugin ###
import deluge
import gtk
from EventLogging.tab_log import LogTabManager

class EventLogging:

    def __init__(self, path, core, interface):
        print "Loading LogEvents plugin..."
        self.manager = core
        self.parent = interface
        # Create an options file and try to load existing Values
        self.config_file = deluge.common.CONFIG_DIR + "/event_logging.conf"
        self.config = deluge.pref.Preferences(self.config_file)
        try:
            self.config.load()
        except IOError:
            # File does not exist
            pass
        self.dialog_initialize = True
        self.glade = gtk.glade.XML(path + "/event_logging_preferences.glade")
        self.dialog = self.glade.get_widget("dialog")
        self.glade.signal_autoconnect({
                                        'toggle_ui': self.toggle_ui
                                      })
        self.viewport = gtk.Viewport()
        self.scrolledWindow = gtk.ScrolledWindow()
        self.scrolledWindow.add(self.viewport)
        self.scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.topWidget = self.scrolledWindow

        self.parentNotebook = self.parent.notebook

        self.parentNotebook.append_page(self.topWidget, gtk.Label(_("Event Log")))
        self.viewport.show()
        self.scrolledWindow.show()
        self.tab_log = LogTabManager(self.viewport, self.manager)
        self.tab_log.build_log_view()
        if self.config.get("enable_finished"):
            self.manager.connect_event(self.manager.constants['EVENT_FINISHED'], self.tab_log.handle_event)
        if self.config.get("enable_peer_error"):
            self.manager.connect_event(self.manager.constants['EVENT_PEER_ERROR'], self.tab_log.handle_event)
        if self.config.get("enable_invalid_request"):
            self.manager.connect_event(self.manager.constants['EVENT_INVALID_REQUEST'], self.tab_log.handle_event)
        if self.config.get("enable_file_error"):
            self.manager.connect_event(self.manager.constants['EVENT_FILE_ERROR'], self.tab_log.handle_event)
        if self.config.get("enable_hash_failed_error"):
            self.manager.connect_event(self.manager.constants['EVENT_HASH_FAILED_ERROR'], self.tab_log.handle_event)
        if self.config.get("enable_peer_ban_error"):
            self.manager.connect_event(self.manager.constants['EVENT_PEER_BAN_ERROR'], self.tab_log.handle_event)
        if self.config.get("enable_fastresume_rejected_error"):
            self.manager.connect_event(self.manager.constants['EVENT_FASTRESUME_REJECTED_ERROR'], self.tab_log.handle_event)
        if self.config.get("enable_tracker_announce"):
            self.manager.connect_event(self.manager.constants['EVENT_TRACKER_ANNOUNCE'], self.tab_log.handle_event)
        if self.config.get("enable_tracker_reply"):
            self.manager.connect_event(self.manager.constants['EVENT_TRACKER_REPLY'], self.tab_log.handle_event)
        if self.config.get("enable_tracker_alert"):
            self.manager.connect_event(self.manager.constants['EVENT_TRACKER_ALERT'], self.tab_log.handle_event)
        if self.config.get("enable_tracker_warning"):
            self.manager.connect_event(self.manager.constants['EVENT_TRACKER_WARNING'], self.tab_log.handle_event)
        if self.config.get("enable_storage_moved"):
            self.manager.connect_event(self.manager.constants['EVENT_STORAGE_MOVED'], self.tab_log.handle_event)
        if self.config.get("enable_piece_finished"):
            self.manager.connect_event(self.manager.constants['EVENT_PIECE_FINISHED'], self.tab_log.handle_event)
        if self.config.get("enable_block_downloading"):
            self.manager.connect_event(self.manager.constants['EVENT_BLOCK_DOWNLOADING'], self.tab_log.handle_event)
        if self.config.get("enable_block_finished"):
            self.manager.connect_event(self.manager.constants['EVENT_BLOCK_FINISHED'], self.tab_log.handle_event)
        if self.config.get("enable_other"):
            self.manager.connect_event(self.manager.constants['EVENT_OTHER'], self.tab_log.handle_event)
        if self.config.get("enable_log_files"):
            self.tab_log.enable_log_files()

    def unload(self):
        if self.config.get("enable_finished"):
            self.manager.disconnect_event(self.manager.constants['EVENT_FINISHED'], self.tab_log.handle_event)
        if self.config.get("enable_peer_error"):
            self.manager.disconnect_event(self.manager.constants['EVENT_PEER_ERROR'], self.tab_log.handle_event)
        if self.config.get("enable_invalid_request"):
            self.manager.disconnect_event(self.manager.constants['EVENT_INVALID_REQUEST'], self.tab_log.handle_event)
        if self.config.get("enable_file_error"):
            self.manager.disconnect_event(self.manager.constants['EVENT_FILE_ERROR'], self.tab_log.handle_event)
        if self.config.get("enable_hash_failed_error"):
            self.manager.disconnect_event(self.manager.constants['EVENT_HASH_FAILED_ERROR'], self.tab_log.handle_event)
        if self.config.get("enable_peer_ban_error"):
            self.manager.disconnect_event(self.manager.constants['EVENT_PEER_BAN_ERROR'], self.tab_log.handle_event)
        if self.config.get("enable_fastresume_rejected_error"):
            self.manager.disconnect_event(self.manager.constants['EVENT_FASTRESUME_REJECTED_ERROR'], self.tab_log.handle_event)
        if self.config.get("enable_tracker_announce"):
            self.manager.disconnect_event(self.manager.constants['EVENT_TRACKER_ANNOUNCE'], self.tab_log.handle_event)
        if self.config.get("enable_tracker_reply"):
            self.manager.disconnect_event(self.manager.constants['EVENT_TRACKER_REPLY'], self.tab_log.handle_event)
        if self.config.get("enable_tracker_alert"):
            self.manager.disconnect_event(self.manager.constants['EVENT_TRACKER_ALERT'], self.tab_log.handle_event)
        if self.config.get("enable_tracker_warning"):
            self.manager.disconnect_event(self.manager.constants['EVENT_TRACKER_WARNING'], self.tab_log.handle_event)
        if self.config.get("enable_storage_moved"):
            self.manager.disconnect_event(self.manager.constants['EVENT_STORAGE_MOVED'], self.tab_log.handle_event)
        if self.config.get("enable_piece_finished"):
            self.manager.disconnect_event(self.manager.constants['EVENT_PIECE_FINISHED'], self.tab_log.handle_event)
        if self.config.get("enable_block_downloading"):
            self.manager.disconnect_event(self.manager.constants['EVENT_BLOCK_DOWNLOADING'], self.tab_log.handle_event)
        if self.config.get("enable_block_finished"):
            self.manager.disconnect_event(self.manager.constants['EVENT_BLOCK_FINISHED'], self.tab_log.handle_event)
        if self.config.get("enable_other"):
            self.manager.disconnect_event(self.manager.constants['EVENT_OTHER'], self.tab_log.handle_event)
        self.tab_log.clear_log_store()
        numPages = self.parentNotebook.get_n_pages()
        for page in xrange(numPages):
            if self.parentNotebook.get_nth_page(page) == self.topWidget:
                self.parentNotebook.remove_page(page)
                break
        self.config.save(self.config_file)

    def update(self):
        pass

    def toggle_ui(self, widget):
        if not self.dialog_initialize:
            value = widget.get_active()
            if widget == self.glade.get_widget("chk_finished"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_FINISHED'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_FINISHED'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_peer_error"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_PEER_ERROR'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_PEER_ERROR'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_invalid_request"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_INVALID_REQUEST'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_INVALID_REQUEST'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_file_error"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_FILE_ERROR'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_FILE_ERROR'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_hash_failed_error"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_HASH_FAILED_ERROR'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_HASH_FAILED_ERROR'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_peer_ban_error"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_PEER_BAN_ERROR'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_PEER_BAN_ERROR'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_fastresume_rejected_error"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_FASTRESUME_REJECTED_ERROR'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_FASTRESUME_REJECTED_ERROR'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_tracker_announce"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_TRACKER_ANNOUNCE'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_TRACKER_ANNOUNCE'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_tracker_reply"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_TRACKER_REPLY'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_TRACKER_REPLY'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_tracker_alert"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_TRACKER_ALERT'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_TRACKER_ALERT'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_tracker_warning"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_TRACKER_WARNING'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_TRACKER_WARNING'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_storage_moved"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_STORAGE_MOVED'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_STORAGE_MOVED'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_piece_finished"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_PIECE_FINISHED'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_PIECE_FINISHED'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_block_downloading"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_BLOCK_DOWNLOADING'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_BLOCK_DOWNLOADING'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_block_finished"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_BLOCK_FINISHED'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_BLOCK_FINISHED'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_other"):
                if value:
                    self.manager.connect_event(self.manager.constants['EVENT_OTHER'], self.tab_log.handle_event)
                else:
                    self.manager.disconnect_event(self.manager.constants['EVENT_OTHER'], self.tab_log.handle_event)
            if widget == self.glade.get_widget("chk_log_files"):
                if value:
                    self.tab_log.enable_log_files()
                else:
                    self.tab_log.disable_log_files()

    def configure(self):
        self.dialog_initialize = True
        try:
            self.glade.get_widget("chk_finished").set_active(self.config.get("enable_finished"))
            self.glade.get_widget("chk_peer_error").set_active(self.config.get("enable_peer_error"))
            self.glade.get_widget("chk_invalid_request").set_active(self.config.get("enable_invalid_request"))
            self.glade.get_widget("chk_file_error").set_active(self.config.get("enable_file_error"))
            self.glade.get_widget("chk_hash_failed_error").set_active(self.config.get("enable_hash_failed_error"))
            self.glade.get_widget("chk_peer_ban_error").set_active(self.config.get("enable_peer_ban_error"))
            self.glade.get_widget("chk_fastresume_rejected_error").set_active(self.config.get("enable_fastresume_rejected_error"))
            self.glade.get_widget("chk_tracker_announce").set_active(self.config.get("enable_tracker_announce"))
            self.glade.get_widget("chk_tracker_reply").set_active(self.config.get("enable_tracker_reply"))
            self.glade.get_widget("chk_tracker_alert").set_active(self.config.get("enable_tracker_alert"))
            self.glade.get_widget("chk_tracker_warning").set_active(self.config.get("enable_tracker_warning"))
            self.glade.get_widget("chk_storage_moved").set_active(self.config.get("enable_storage_moved"))
            self.glade.get_widget("chk_piece_finished").set_active(self.config.get("enable_piece_finished"))
            self.glade.get_widget("chk_block_downloading").set_active(self.config.get("enable_block_downloading"))
            self.glade.get_widget("chk_block_finished").set_active(self.config.get("enable_block_finished"))
            self.glade.get_widget("chk_other").set_active(self.config.get("enable_other"))
            self.glade.get_widget("chk_log_files").set_active(self.config.get("enable_log_files"))
        except:
            self.glade.get_widget("chk_finished").set_active(False)
            self.glade.get_widget("chk_peer_error").set_active(False)
            self.glade.get_widget("chk_invalid_request").set_active(False)
            self.glade.get_widget("chk_file_error").set_active(False)
            self.glade.get_widget("chk_hash_failed_error").set_active(False)
            self.glade.get_widget("chk_peer_ban_error").set_active(False)
            self.glade.get_widget("chk_fastresume_rejected_error").set_active(False)
            self.glade.get_widget("chk_tracker_announce").set_active(False)
            self.glade.get_widget("chk_tracker_reply").set_active(False)
            self.glade.get_widget("chk_tracker_alert").set_active(False)
            self.glade.get_widget("chk_tracker_warning").set_active(False)
            self.glade.get_widget("chk_storage_moved").set_active(False)
            self.glade.get_widget("chk_piece_finished").set_active(False)
            self.glade.get_widget("chk_block_downloading").set_active(False)
            self.glade.get_widget("chk_block_finished").set_active(False)
            self.glade.get_widget("chk_other").set_active(False)
            self.glade.get_widget("chk_log_files").set_active(False)
        self.dialog_initialize = False
        self.dialog.show()
        response = self.dialog.run()
        self.dialog.hide()
        if response:
            self.config.set("enable_finished", self.glade.get_widget("chk_finished").get_active())
            self.config.set("enable_peer_error", self.glade.get_widget("chk_peer_error").get_active())
            self.config.set("enable_invalid_request", self.glade.get_widget("chk_invalid_request").get_active())
            self.config.set("enable_file_error", self.glade.get_widget("chk_file_error").get_active())
            self.config.set("enable_hash_failed_error", self.glade.get_widget("chk_hash_failed_error").get_active())
            self.config.set("enable_peer_ban_error", self.glade.get_widget("chk_peer_ban_error").get_active())
            self.config.set("enable_fastresume_rejected_error", self.glade.get_widget("chk_fastresume_rejected_error").get_active())
            self.config.set("enable_tracker_announce", self.glade.get_widget("chk_tracker_announce").get_active())
            self.config.set("enable_tracker_reply", self.glade.get_widget("chk_tracker_reply").get_active())
            self.config.set("enable_tracker_alert", self.glade.get_widget("chk_tracker_alert").get_active())
            self.config.set("enable_tracker_warning", self.glade.get_widget("chk_tracker_warning").get_active())
            self.config.set("enable_storage_moved", self.glade.get_widget("chk_storage_moved").get_active())
            self.config.set("enable_piece_finished", self.glade.get_widget("chk_piece_finished").get_active())
            self.config.set("enable_block_downloading", self.glade.get_widget("chk_block_downloading").get_active())
            self.config.set("enable_block_finished", self.glade.get_widget("chk_block_finished").get_active())
            self.config.set("enable_other", self.glade.get_widget("chk_other").get_active())
            self.config.set("enable_log_files", self.glade.get_widget("chk_log_files").get_active())
