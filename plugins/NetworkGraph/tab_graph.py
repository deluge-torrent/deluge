# -*- coding: utf-8 -*-
#
# tab_graph.py
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
import pango
import cairo
import math
import deluge.common

class GraphTabManager:
    def __init__(self, scrolledWindow, image, pangoLayout, manager):
        self.scrolledWindow = scrolledWindow
        self.image = image
        self.pangoLayout = pangoLayout
        self.manager = manager
        self.length = 60

        self.width  = -1
        self.height = -1

        self.savedUpSpeeds   = []
        self.savedDownSpeeds = []

        self.download_line = None
        self.download_line_color = None
        self.download_fill = None
        self.download_fill_color = None
        self.upload_line = None
        self.upload_line_color = None
        self.upload_fill = None
        self.upload_fill_color = None
        self.max_selected = None
        self.mean_selected = None
        self.legend_selected = None
        self.line_size = 4

    #Download
    def enable_download_line(self):
        self.download_line = True

    def disable_download_line(self):
        self.download_line = False

    def enable_download_fill(self):
        self.download_fill = True

    def disable_download_fill(self):
        self.download_fill = False

    #Upload
    def enable_upload_line(self):
        self.upload_line = True

    def disable_upload_line(self):
        self.upload_line = False

    def enable_upload_fill(self):
        self.upload_fill = True

    def disable_upload_fill(self):
        self.upload_fill = False

    #Mean
    def enable_mean(self):
        self.mean_selected = True

    def disable_mean(self):
        self.mean_selected = False

    #Max
    def enable_max(self):
        self.max_selected = True
    
    def disable_max(self):
        self.max_selected = False

    #Legend
    def enable_legend(self):
        self.legend_selected = True

    def disable_legend(self):
        self.legend_selected = False
        

    def update_graph_store(self):
        session_info = self.manager.get_state()
        self.savedUpSpeeds.insert(0, session_info['upload_rate'])
        if len(self.savedUpSpeeds) > self.length:
            self.savedUpSpeeds.pop()
        self.savedDownSpeeds.insert(0, session_info['download_rate'])
        if len(self.savedDownSpeeds) > self.length:
            self.savedDownSpeeds.pop()

    def update_graph_view(self):   
        extraWidth  = self.scrolledWindow.get_vscrollbar().get_allocation().width  * 1.5
        extraHeight = self.scrolledWindow.get_hscrollbar().get_allocation().height * 1.5
        allocation = self.scrolledWindow.get_allocation()
        allocation.width  = int(allocation.width)  - extraWidth
        allocation.height = int(allocation.height) - extraHeight
        # Don't try to allocate a size too small, or you might crash
        if allocation.width < 2 or allocation.height < 2:
            return

#        savedDownSpeeds = [1,2,3,2,1]
#        savedUpSpeeds = [5,8,0,0,1,2]

#        allocation = self.image.get_allocation()
#        allocation.width  = 300
#        allocation.height = 200

        if not allocation.width == self.width or not allocation.height == self.height:
#            print "New Pixmap!"
            self.width  = allocation.width
            self.height = allocation.height

            self.networkPixmap = gtk.gdk.Pixmap(None, self.width,self.height,gtk.gdk.visual_get_system().depth)
            self.image.set_from_pixmap(self.networkPixmap, None)
            self.ctx = self.networkPixmap.cairo_create()

        self.networkPixmap.draw_rectangle(self.image.get_style().white_gc,True, 0, 0, self.width, self.height)

        if (self.download_fill or self.download_line) and (self.upload_fill or self.upload_line):
            maxSpeed = max(max(self.savedDownSpeeds),max(self.savedUpSpeeds))
            meanSpeed = max(sum(self.savedUpSpeeds)  /len(self.savedUpSpeeds), sum(self.savedDownSpeeds)/len(self.savedDownSpeeds))
        elif self.download_fill or self.download_line:
            maxSpeed = max(self.savedDownSpeeds)
            meanSpeed = sum(self.savedDownSpeeds)/len(self.savedDownSpeeds)
        elif self.upload_fill or self.upload_line:
            maxSpeed = max(self.savedUpSpeeds)
            meanSpeed = sum(self.savedUpSpeeds)  /len(self.savedUpSpeeds)
        else:
            maxSpeed = 0
        
        if self.legend_selected:
            self.drawLegend()

        if maxSpeed > 0:
            if self.download_fill:
                self.drawSpeedPoly(self.savedDownSpeeds,self.download_fill_color, maxSpeed, True)

            if self.download_line:
                self.drawSpeedPoly(self.savedDownSpeeds,self.download_line_color,maxSpeed, False) 

            if self.upload_fill:
                self.drawSpeedPoly(self.savedUpSpeeds,self.upload_fill_color,maxSpeed, True)

            if self.upload_line:
                self.drawSpeedPoly(self.savedUpSpeeds,self.upload_line_color,maxSpeed, False)

            if self.max_selected:
                self.drawText(deluge.common.fspeed(maxSpeed),self.image.get_style().black_gc,4,2)
            
            if self.mean_selected:
                self.pangoLayout.set_text(deluge.common.fspeed(meanSpeed))
                self.networkPixmap.draw_layout(self.image.get_style().black_gc,
                                                4,
                                                int(self.height - 1 - ((self.height-28)*meanSpeed/maxSpeed)),
                                                self.pangoLayout)
                self.networkPixmap.draw_line(self.image.get_style().black_gc,
                                                0,
                                                int(self.height - ((self.height-28)*meanSpeed/maxSpeed)),
                                                self.width,
                                                int(self.height - ((self.height-28)*meanSpeed/maxSpeed)))

        self.networkPixmap.draw_rectangle(self.image.get_style().black_gc,False, 0, 0, self.width-1, self.height-1)
        self.image.queue_draw()

    def tracePath(self, speeds, maxSpeed):
        lineWidth = self.line_size

        self.ctx.set_line_width(lineWidth)
        self.ctx.move_to(self.width + lineWidth,self.height + lineWidth)
        self.ctx.line_to(self.width + lineWidth,int(self.height-((self.height-28)*speeds[0]/maxSpeed)))

        for i in range(len(speeds)):
            self.ctx.line_to(int(self.width-1-((i*self.width)/(self.length-1))),int(self.height-1-((self.height-28)*speeds[i]/maxSpeed)))

        self.ctx.line_to(int(self.width-1-(((len(speeds)-1)*self.width)/(self.length-1))),int(self.height)-1 + lineWidth)
        self.ctx.close_path()

    def drawSpeedPoly(self, speeds, color, maxSpeed, fill):
        self.tracePath(speeds, maxSpeed)
        self.ctx.set_source_rgba(color[0],color[1],color[2], color[3])

        if fill:
            self.ctx.fill()
        else:
            self.ctx.stroke()
    
    def drawLegend(self):
        showDown = self.download_fill or self.download_line
        showUp = self.upload_fill or self.upload_line
        downBox_X = self.width-113

        if showDown and showUp:
            self.networkPixmap.draw_line(self.image.get_style().black_gc,self.width-186,1,self.width-186,21)
            self.networkPixmap.draw_line(self.image.get_style().black_gc,self.width-185,21,self.width-1,21)
            self.drawText("Download:",self.image.get_style().black_gc,self.width-181,2)
            self.drawText("Upload:",self.image.get_style().black_gc,self.width-81,2)
        elif showDown:
            self.networkPixmap.draw_line(self.image.get_style().black_gc,self.width-103,1,self.width-103,21)
            self.networkPixmap.draw_line(self.image.get_style().black_gc,self.width-102,21,self.width-1,21)
            self.drawText("Download:",self.image.get_style().black_gc,self.width-98,2)
            downBox_X = self.width-30
        elif showUp:
            self.networkPixmap.draw_line(self.image.get_style().black_gc,self.width-86,1,self.width-86,21)
            self.networkPixmap.draw_line(self.image.get_style().black_gc,self.width-85,21,self.width-1,21)
            self.drawText("Upload:",self.image.get_style().black_gc,self.width-81,2)

        if self.download_fill and self.download_line:
            self.drawRect(self.download_line_color,downBox_X,5,12,12)
            self.drawRect(self.download_fill_color,downBox_X+12,5,12,12)
        elif self.download_fill:
            self.drawRect(self.download_fill_color,downBox_X,5,24,12)
        elif self.download_line:
            self.drawRect(self.download_line_color,downBox_X,5,24,12)

        if self.upload_fill and self.upload_line:
            self.drawRect(self.upload_line_color,self.width-30,5,12,12)
            self.drawRect(self.upload_fill_color,self.width-18,5,12,12)
        elif self.upload_fill:
            self.drawRect(self.upload_fill_color,self.width-30,5,24,12)
        elif self.upload_line:
            self.drawRect(self.upload_line_color,self.width-30,5,24,12)

    def drawText(self,text,color,x,y):
        self.pangoLayout.set_text(text)
        self.networkPixmap.draw_layout(color,x,y,self.pangoLayout)
    
    def drawRect(self,color,x,y,height,width):
        self.ctx.set_source_rgba(color[0],color[1],color[2],color[3],)
        self.ctx.rectangle(x,y,height,width)
        self.ctx.fill()








