#graph.py
"""
port of old plugin by markybob.
"""
import cairo
import math
from deluge.log import LOG as log
import deluge.common
import time
from deluge.ui.client import aclient

class NetworkGraph:
    def __init__(self):

        self.width = 100
        self.height = 100

        self.length = 150

        self.savedUpSpeeds   = []
        self.savedDownSpeeds = []

        self.download_line = True
        self.download_fill = True
        self.upload_line = True
        self.upload_fill = True
        self.download_line_color = (0,  0.75,0,   1.0)
        self.download_fill_color = (0.6 ,1.1 ,   0.6, 1.0)
        self.upload_line_color = (0,   0,   1.0,  0.75)
        self.upload_fill_color = (0.43,0.43,1.1,  0.5)
        self.mean_selected = True
        self.legend_selected = True
        self.max_selected = True
        self.line_size = 4
        self.black = (0, 0 , 0,)
        self.interval = 2000 #2secs
        self.text_bg =  (255, 255 , 255, 128) #prototyping.

    def async_request(self):
        """
        convenience method, see test.py
        """
        aclient.graph_get_upload(self.set_upload)
        aclient.graph_get_download(self.set_download)
        aclient.graph_get_config(self.set_config)

    #async callbacks:
    def set_config(self, config):
        self.length = config["stats_length"]
        self.interval = config["update_interval"]

    def set_upload(self , upload):
        self.savedUpSpeeds = upload

    def set_download(self , download):
        self.savedDownSpeeds = download


    def draw(self, width, height):
        self.width  = width
        self.height = height

        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width,self.height)
        self.ctx = cairo.Context(self.surface)

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


        if maxSpeed > 0:

            if self.max_selected:
                self.drawText(deluge.common.fspeed(maxSpeed),4,2)

            if self.download_fill:
                self.drawSpeedPoly(self.savedDownSpeeds,self.download_fill_color, maxSpeed, True)

            if self.download_line:
                self.drawSpeedPoly(self.savedDownSpeeds,self.download_line_color,maxSpeed, False)

            if self.upload_fill:
                self.drawSpeedPoly(self.savedUpSpeeds,self.upload_fill_color,maxSpeed, True)

            if self.upload_line:
                self.drawSpeedPoly(self.savedUpSpeeds,self.upload_line_color,maxSpeed, False)


            if self.mean_selected:
                mean = int(self.height - 1 - ((self.height-28)*meanSpeed/maxSpeed))

                self.drawLine(self.black, 0,mean, self.width, mean)
                self.drawText(deluge.common.fspeed(meanSpeed), 4, mean - 12 - 2)

        if self.legend_selected:
            self.drawLegend()
        return self.surface


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

        self.drawText("Download:", self.width-180,3)
        self.drawText("Upload:", self.width-80,3)

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

        if True:
            txt_end = time.strftime("%H:%M:%S")
            txt_start = time.strftime("%H:%M:%S",time.localtime(time.time() -  self.length * (self.interval / 1000.0) ))
            self.length * self.interval
            self.drawText(txt_end, self.width-60,self.height  - 20)
            self.drawText(txt_start, 4 ,self.height  - 20)


    def drawText(self,text,x,y):
        self.ctx.set_font_size(12)
        self.ctx.move_to(x, y +12)
        self.ctx.set_source_rgba(*self.black)
        self.ctx.show_text(text)

    def drawRect(self,color,x,y,height,width):
        self.ctx.set_source_rgba(color[0],color[1],color[2],color[3],)
        self.ctx.rectangle(x,y,height,width)
        self.ctx.fill()

    def drawLine(self,color,x1,y1,x2,y2):
        self.ctx.set_source_rgba(*color)
        self.ctx.set_line_width(1)
        self.ctx.move_to(x1, y1)
        self.ctx.line_to(x2, y2)
        self.ctx.stroke()

if __name__ == "__main__":
    import test


