import gtk
import pango

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
            
            self.networkPixmap = gtk.gdk.Pixmap(None, self.width, 
                self.height, gtk.gdk.visual_get_system().depth)
            self.image.set_from_pixmap(self.networkPixmap, None)
            self.ctx = self.networkPixmap.cairo_create()
            
        self.networkPixmap.draw_rectangle(self.image.get_style().white_gc,True, 0, 0, self.width, self.height)
        
        maxSpeed = max(max(self.savedDownSpeeds),max(self.savedUpSpeeds))
            
        if maxSpeed == 0:
            return
        
        maxSpeed = maxSpeed*1.1 # Give some extra room on top
        
        self.drawSpeedPoly(self.savedDownSpeeds, (0.5,1,   0.5, 1.0),    maxSpeed, True)
        self.drawSpeedPoly(self.savedDownSpeeds, (0,  0.75,0,   1.0),    maxSpeed, False)
        
        self.drawSpeedPoly(self.savedUpSpeeds,   (0.33,0.33,1.0,  0.5),  maxSpeed, True)
        self.drawSpeedPoly(self.savedUpSpeeds,   (0,   0,   1.0,  0.75), maxSpeed, False)
        
        meanUpSpeed   = sum(self.savedUpSpeeds)  /len(self.savedUpSpeeds)
        meanDownSpeed = sum(self.savedDownSpeeds)/len(self.savedDownSpeeds)
        shownSpeed    = max(meanUpSpeed, meanDownSpeed)
        
        import deluge.common
        
        self.pangoLayout.set_text(deluge.common.fspeed(shownSpeed))
        self.networkPixmap.draw_layout(self.image.get_style().black_gc,
                                                 4,
                                                 int(self.height - 1 - (self.height*shownSpeed/maxSpeed)),
                                                 self.pangoLayout)
        
        self.networkPixmap.draw_line(self.image.get_style().black_gc,
                                                 0,
                                                 int(self.height - (self.height*shownSpeed/maxSpeed)),
                                                 self.width,
                                                 int(self.height - (self.height*shownSpeed/maxSpeed)))
        
        self.networkPixmap.draw_rectangle(self.image.get_style().black_gc,False, 0, 0, self.width-1, self.height-1)
        
        self.image.queue_draw()
        
    def tracePath(self, speeds, maxSpeed):
        lineWidth = 4

        self.ctx.set_line_width(lineWidth)

        self.ctx.move_to(self.width + lineWidth,self.height + lineWidth)
        self.ctx.line_to(self.width + lineWidth,int(self.height-(self.height*speeds[0]/maxSpeed)))

        for i in range(len(speeds)):
            self.ctx.line_to(int(self.width-1-((i*self.width)/(self.length-1))),
                                    int(self.height-1-(self.height*speeds[i]/maxSpeed)))

        self.ctx.line_to(int(self.width-1-(((len(speeds)-1)*self.width)/(self.length-1))),
                                int(self.height)-1 + lineWidth)

        self.ctx.close_path()

    def drawSpeedPoly(self, speeds, color, maxSpeed, fill):

        self.tracePath(speeds, maxSpeed)
        self.ctx.set_source_rgba(color[0],color[1],color[2], color[3])

        if fill:
            self.ctx.fill()
        else:
            self.ctx.stroke()
