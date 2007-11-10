# -*- coding: utf-8 -*-
#
# tab_details.py
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

import common
import gtk

class DetailsTabManager(object):
    def __init__(self, glade, manager):
        self.manager = manager
        
        self.paused_unique_id = None
        
        # Look into glade's widget prefix function
        self.progress_bar = glade.get_widget("progressbar")
        self.custom_progress = glade.get_widget("custom_progress")
        self.custom_progress.connect("expose_event",self.paint_customprogress)
        self.name = glade.get_widget("summary_name")
        self.total_size = glade.get_widget("summary_total_size")
        self.num_files = glade.get_widget("summary_num_files")
        self.pieces = glade.get_widget("summary_pieces")
        self.availability = glade.get_widget("summary_availability")
        self.total_downloaded = glade.get_widget("summary_total_downloaded")
        self.total_uploaded = glade.get_widget("summary_total_uploaded")
        self.download_speed = glade.get_widget("summary_download_speed")
        self.upload_speed = glade.get_widget("summary_upload_speed")
        self.seeders = glade.get_widget("summary_seeders")
        self.peers = glade.get_widget("summary_peers")
        self.percentage_done = glade.get_widget("summary_percentage_done")
        self.share_ratio = glade.get_widget("summary_share_ratio")
        self.tracker = glade.get_widget("summary_tracker")
        self.tracker_status = glade.get_widget("summary_tracker_status")
        self.next_announce = glade.get_widget("summary_next_announce")
        self.eta = glade.get_widget("summary_eta")
        self.torrent_path = glade.get_widget("summary_torrent_path")
        self.advanced_progressbar=glade.get_widget("advanced_progressbar")

       	self.last_state=None
        self.prefchanged_progress()
        self.manager.config.onValueChanged('use_advanced_bar',self.prefchanged_progress)

    def prefchanged_progress(self):
        self.use_advanced_bar=self.manager.config.get("use_advanced_bar")
        if self.use_advanced_bar:
            self.progress_bar.hide()
            self.advanced_progressbar.show()
        else:
            self.progress_bar.show()
            self.advanced_progressbar.hide()

    # arg1 and arg2 are additional data which we do not need. Most probably
    #   arg1=widghet, and arg2=event specific data
    #   If anybody knows of documentation which includes the expose_event
    #   in PyGtk would be glad to see it. - hirak99        
    def paint_customprogress(self,arg1=None,arg2=None):
	# Draw the custom progress bar
	progress_window=self.custom_progress.window
	colormap=self.custom_progress.get_colormap()
	gc=progress_window.new_gc()
	size=progress_window.get_size()
	progress_window.begin_paint_rect(gtk.gdk.Rectangle(0,0,size[0],size[1]))
	height=size[1]
	if height>25: height=25
	top=(size[1]-height)/2
	gc.set_foreground(colormap.alloc_color('#F0F0FF'))
	progress_window.draw_rectangle(gc,True,0,top,size[0],height-1)
	gc.set_foreground(colormap.alloc_color('#A0A0AF'))
	progress_window.draw_line(gc,0,top+4,size[0],top+4)
	state=self.last_state
	if state!=None:
		gc.set_foreground(colormap.alloc_color('#2020FF'))
		progress_window.draw_rectangle(gc,True,0,top,int(size[0]*float(state['progress'])),4)
		num_pieces=state["num_pieces"]
		for pieces_range in state['pieces']:
			range_first=pieces_range[0]*size[0]/num_pieces
			range_length=((pieces_range[1]-pieces_range[0]+1)*size[0]/num_pieces)
			if range_length==0:
				range_length=1
				gc.set_foreground(colormap.alloc_color('#8080FF'))
			else:
				gc.set_foreground(colormap.alloc_color('#2020FF'))
			progress_window.draw_rectangle(gc,True,range_first,top+5,range_length,height-5)
	gc.set_foreground(colormap.alloc_color('dim gray'))
	progress_window.draw_line(gc,0,top,0,top+height)
	progress_window.draw_line(gc,0,top,size[0],top)
	gc.set_foreground(colormap.alloc_color('white'))
	progress_window.draw_line(gc,0,top+height,size[0]-1,top+height)
	progress_window.draw_line(gc,size[0]-1,top,size[0]-1,top+height)
	progress_window.end_paint()
	# Done drawing custom progress bar
	
    def update(self, unique_id):
        state = self.manager.get_torrent_state(unique_id)

        # Update selected files size, tracker, tracker status and next 
        # announce no matter what status of the torrent is
        self.total_size.set_text(common.fsize(state["total_wanted"]))
        self.tracker.set_text(str(state["tracker"]))
        # At this time we still may not receive EVENT_TRACKER so there
        # could be no tracker_status yet.
        if "tracker_status" in state:
            self.tracker_status.set_text(state["tracker_status"])
        self.next_announce.set_text(str(state["next_announce"]))
        
        if state['is_paused']:
            if not self.paused_unique_id:
                # Selected torrent just paused, zero data now and don't 
                # update it anymore on each update()
                state['num_seeds'] = state['total_seeds'] = \
                    state['num_peers'] = state['total_peers'] = \
                    state['download_rate'] = state['upload_rate'] = 0
                    
                self.paused_unique_id = unique_id
            elif self.paused_unique_id != unique_id:
                # User selected another paused torrent with unique_id after
                # paused torrent with self.paused_unique_id, so update
                # currently selected unique_id and do full update of details
                self.paused_unique_id = unique_id
            else:
                # If we already updated paused torrent - do nothing more
                return
        else:
            self.paused_unique_id = None
        
        self.name.set_text(state['name'])
        self.num_files.set_text(str(state['num_files']))
        self.pieces.set_text('%s x %s' % (state["num_pieces"], 
                                          common.fsize(state["piece_length"])))
        self.availability.set_text('%.3f' % state["distributed_copies"])
        self.total_downloaded.set_text('%s (%s)' % \
            (common.fsize(state["total_done"]),
             common.fsize(state["total_payload_download"])))
        self.total_uploaded.set_text('%s (%s)' % \
            (common.fsize(self.manager.unique_IDs[unique_id].uploaded_memory+\
                          state["total_payload_upload"]),
             common.fsize(state["total_payload_upload"])))
        self.download_speed.set_text(common.fspeed(state["download_rate"]))
        self.upload_speed.set_text(common.fspeed(state["upload_rate"]))
        self.seeders.set_text(common.fseed(state))
        self.peers.set_text(common.fpeer(state))
#        self.progress_bar.set_fraction(float(state['progress']))
#        self.progress_bar.set_text(common.fpcnt(state["progress"]))
        self.last_state=state
        if self.use_advanced_bar:
            self.paint_customprogress()
        else:
            self.progress_bar.set_fraction(float(state['progress']))
            self.progress_bar.set_text(common.fpcnt(state["progress"]))


        self.eta.set_text(common.estimate_eta(state))
        self.share_ratio.set_text('%.3f' % self.manager.calc_ratio(unique_id,
                                                                    state))
        self.torrent_path.set_text(self.manager.get_torrent_path(unique_id))
        
    def clear(self):
        self.name.set_text("")
        self.total_size.set_text("")
        self.num_files.set_text("")
        self.pieces.set_text("")
        self.availability.set_text("")
        self.total_downloaded.set_text("")
        self.total_uploaded.set_text("")
        self.download_speed.set_text("")
        self.upload_speed.set_text("")
        self.seeders.set_text("")
        self.peers.set_text("")
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("")
        self.share_ratio.set_text("")
        self.tracker.set_text("")
        self.tracker_status.set_text("")
        self.next_announce.set_text("")
        self.eta.set_text("")
        self.torrent_path.set_text("")
