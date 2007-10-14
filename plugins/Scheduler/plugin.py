import deluge.common, deluge.pref, gtk, copy, pickle, time

class plugin_Scheduler:
    def __init__(self, path, deluge_core, deluge_interface):
        self.path = path
        self.core = deluge_core
        self.interface = deluge_interface

        self.days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.conf_file = deluge.common.CONFIG_DIR + "/scheduler.conf"
        self.config = deluge.pref.Preferences()
        self.button_state_temp = [[0] * 7 for dummy in xrange(24)]
        self.status = -1
        self.globalactivetor = self.config.get("max_active_torrents")
        self.globaldlmax = self.config.get("max_download_speed")
        self.globalulmax = self.config.get("max_upload_speed")

        #Load config
        try:
            reader = open(self.conf_file, "rb")
            data = pickle.load(reader)
            self.button_state = data[0]
            self.dllimit = float(data[1][0])
            self.ullimit = float(data[1][1])
            reader.close()
        except:
            self.button_state = [[0] * 7 for dummy in xrange(24)]
            self.dllimit = float(self.globaldlmax)
            self.ullimit = float(self.globalulmax)
        self.interface.apply_prefs()

    def unload(self):
        self.resume()
        self.unlimit()

    def update(self):
        time_now = time.localtime(time.time())
        if self.status is not self.button_state[time_now[3]][time_now[6]]:
            self.status = self.button_state[time_now[3]][time_now[6]]

            if self.status == 0:
                self.resume()
                self.unlimit()
            elif self.status == 1:
                self.resume()
            elif self.status == 2:
                self.pause()

        if self.status == 1:
            self.limit()

    def pause(self):
        self.config.set("max_active_torrents", 0)
        self.core.apply_queue()

    def resume(self):
        self.config.set("max_active_torrents", self.globalactivetor)
        self.core.apply_queue()

    def limit(self):
        self.config.set("max_download_speed", float(self.dllimit))
        self.config.set("max_upload_speed", float(self.ullimit))

    def unlimit(self):
        self.config.set("max_download_speed", float(self.globaldlmax))
        self.config.set("max_upload_speed", float(self.globalulmax))
        self.interface.apply_prefs()

    #Configuration dialog
    def configure(self, window):
        global scheduler_select

        self.button_state_temp = copy.deepcopy(self.button_state)

        #dialog
        dialog = gtk.Dialog(_("Scheduler Settings"))
        dialog.set_default_size(600, 270)

        #buttons
        cancel_button = dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        ok_button = dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
        #text
        hover_text = gtk.Label()

        dllimit_label = gtk.Label(_("Limit download to:"))
        ullimit_label = gtk.Label(_("Limit upload to:"))

        #Select Widget
        drawing = scheduler_select(self.button_state_temp, hover_text, self.days)

        #boxes
        vbox_main = gtk.VBox()
        hbox_main = gtk.HBox()
        vbox_sub = gtk.VBox()
        hbox_key = gtk.HBox()
        hbox_info = gtk.HBox()
        hbox_limit = gtk.HBox()

        #seperator
        sep = gtk.HSeparator()

        #spinbuttons

        dlinput = gtk.SpinButton()
        dlinput.set_numeric(True)    
        dlinput.set_range(-1, 2048)
        dlinput.set_increments(1, 10)
        if self.dllimit != -1:
            dlinput.set_value(float(self.dllimit))
        else:
            dlinput.set_value(float(-1))
        ulinput = gtk.SpinButton()
        ulinput.set_numeric(True)
        ulinput.set_range(-1, 1024)
        ulinput.set_increments(1, 10)
        if self.ullimit != -1:
            ulinput.set_value(float(self.ullimit))
        else:
            ulinput.set_value(float(-1))

        #pack
        dialog.vbox.pack_start(vbox_main)

        vbox_main.pack_start(hbox_main)
        vbox_main.pack_start(hover_text, False, True)
        vbox_main.pack_start(hbox_key, False, True)
        vbox_main.pack_start(hbox_info, False, True)
        vbox_main.pack_start(sep, False, True)
        vbox_main.pack_start(hbox_limit, False, True, 5)

        hbox_main.pack_start(vbox_sub, False, True, 5)
        hbox_main.pack_start(drawing)

        hbox_key.pack_start(gtk.Label(_("Yellow is limited, red is stopped and \
green is unlimited.")), True, False)
        hbox_info.pack_start(gtk.Label(_("When set to -1 (unlimited), the global limits in Deluge's preferences \
will be obeyed.")), True, False)

        hbox_limit.pack_start(dllimit_label, True, False)
        hbox_limit.pack_start(dlinput, True, False)
        hbox_limit.pack_start(ullimit_label, True, False)
        hbox_limit.pack_start(ulinput, True, False)

        for index in xrange(len(self.days)):
            vbox_sub.pack_start(gtk.Label(self.days[index]))

        #show
        dialog.show_all()

        #Save config    
        if dialog.run() == -5:
            self.status = -1
            self.button_state = copy.deepcopy(drawing.button_state)
            if dlinput.get_value() != -1:
                self.dllimit = float(dlinput.get_value())
            else:
                self.dllimit = float(dlinput.get_value())                
            if ulinput.get_value() != -1:
                self.ullimit = float(ulinput.get_value())
            else:
                self.ullimit = float(ulinput.get_value())
            self.interface.apply_prefs()

            writer = open(self.conf_file, "wb")
            pickle.dump([drawing.button_state,[self.dllimit, self.ullimit]], writer)
            writer.close()

        dialog.destroy()

class scheduler_select(gtk.DrawingArea):

    #connect signals - varaibles
    def __init__(self, data, label, days):
        gtk.DrawingArea.__init__(self)
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.LEAVE_NOTIFY_MASK)

        self.connect("expose_event", self.expose)
        self.connect("button_press_event", self.mouse_down)
        self.connect("button_release_event", self.mouse_up)
        self.connect("motion_notify_event", self.mouse_hover)
        self.connect("leave_notify_event", self.mouse_leave)

        self.colors = [[115.0/255, 210.0/255, 22.0/255], [237.0/255, 212.0/255, 0.0/255], [204.0/255, 0.0/255, 0.0/255]]
        self.button_state = data
        self.button_state_temp = [[0] * 7 for dummy in xrange(24)]
        self.start_point = [0,0]
        self.hover_point = [-1,-1]
        self.hover_label = label
        self.hover_days = days
        self.mouse_press = False

    #redraw the whole thing
    def expose(self, widget, event):
        self.context = self.window.cairo_create()
        self.context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        self.context.clip()

        width = self.window.get_size()[0]
        height = self.window.get_size()[1]

        for y in xrange(7):
            for x in xrange(24):
                self.context.set_source_rgba(self.colors[self.button_state[x][y]][0], self.colors[self.button_state[x][y]][1], self.colors[self.button_state[x][y]][2], 0.7)
                self.context.rectangle(width*(6*x/145.0+1/145.0), height*(6*y/43.0+1/43.0), 5*width/145.0, 5*height/43.0)
                self.context.fill_preserve()
                self.context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
                self.context.stroke()

    #coordinates --> which box
    def get_point(self, event):
        size = self.window.get_size()
        x = int((event.x-size[0]*0.5/145.0)/(6*size[0]/145.0))
        y = int((event.y-size[1]*0.5/43.0)/(6*size[1]/43.0))

        if x > 23: x = 23
        elif x < 0: x = 0
        if y > 6: y = 6
        elif y < 0: y = 0

        return [x,y]

    #mouse down
    def mouse_down(self, widget, event):
        self.mouse_press = True
        self.start_point = self.get_point(event)
        self.button_state_temp = copy.deepcopy(self.button_state)

    #if the same box -> change it
    def mouse_up(self, widget, event):
        self.mouse_press = False
        end_point = self.get_point(event)

        #change color on mouseclick depending on the button
        if end_point[0] is self.start_point[0] and end_point[1] is self.start_point[1]:
            if event.button == 1:
                self.button_state[end_point[0]][end_point[1]] += 1
                if self.button_state[end_point[0]][end_point[1]] > 2:
                    self.button_state[end_point[0]][end_point[1]] = 0
            elif event.button == 3:
                self.button_state[end_point[0]][end_point[1]] -= 1
                if self.button_state[end_point[0]][end_point[1]] < 0:
                    self.button_state[end_point[0]][end_point[1]] = 2
            self.queue_draw()
        
    #if box changed and mouse is pressed draw all boxes from start point to end point
    #set hover text etc..
    def mouse_hover(self, widget, event):
        if self.get_point(event) != self.hover_point:
            self.hover_point = self.get_point(event)

            self.hover_label.set_text(self.hover_days[self.hover_point[1]] + " " + str(self.hover_point[0]) + ":00 - " + str(self.hover_point[0]) + ":59")

            if self.mouse_press == True:
                self.button_state = copy.deepcopy(self.button_state_temp)

                points = [[self.hover_point[0], self.start_point[0]], [self.hover_point[1], self.start_point[1]]]

                for x in xrange(min(points[0]), max(points[0])+1):
                    for y in xrange(min(points[1]), max(points[1])+1):
                        self.button_state[x][y] = self.button_state[self.start_point[0]][self.start_point[1]]

                self.queue_draw()

    #clear hover text on mouse leave
    def mouse_leave(self, widget, event):
        self.hover_label.set_text("")
        self.hover_point = [-1,-1]
