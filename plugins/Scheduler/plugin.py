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
        self.prevact = None

        #Load config
        self.button_state = None
        self.dllimit = self.ullimit = None
        self.dlmax = self.ulmax = None
        try:
            reader = open(self.conf_file, "rb")
            data = pickle.load(reader)
            self.button_state = data[0]
            self.dllimit = float(data[1][0])
            self.ullimit = float(data[1][1])
            self.dlmax = float(data[1][2])
            self.ulmax = float(data[1][3])
            reader.close()
        except:
            if self.button_state is None:
                self.button_state = [[0] * 7 for dummy in xrange(24)]
            gdl = self.config.get("max_download_speed")
            gul = self.config.get("max_upload_speed")
            if self.dllimit is None:
                self.dllimit = float(gdl)
            if self.ullimit is None:
                self.ullimit = float(gul)
            if self.dlmax is None:
                self.dlmax = float(gdl)
            if self.ulmax is None:
                self.ulmax = float(gul)

        now = time.localtime(time.time())
        self.status = self.button_state[now[3]][now[6]]
        self.prevhour = now[3]

        self._state(self.status)

    def unload(self):
        self.status = -1
        self.resume()
        self.unlimit()

    def _getglobals(self):
        # Only run if plugin is not paused
        if self.status < 2:
            gdl = self.config.get("max_download_speed")
            gul = self.config.get("max_upload_speed")
            if self.status == 0 and (self.dlmax != gdl or self.ulmax != gul):
                self.dlmax = gdl
                self.ulmax = gul
            elif self.status == 1 and (self.dllimit != gdl or self.ullimit != gul):
                self.dllimit = gdl
                self.ullimit = gul

    def _state(self,state):
        if state == 0:
            self.unlimit()
        elif state == 1:
            self.limit()
        elif state == 2:
            self.pause()
        # If we're moving from paused
        if state < 2 and self.status == 2:
            self.resume()
        self.status = state
        # Update the settings
        self.interface.apply_prefs()

    def update(self):
        # Only do stuff if the status is valid
        if self.status < 0:
            return

        # Apply any changes that have been made to the global config
        self._getglobals()
        now = time.localtime(time.time())
        if now[3] != self.prevhour:
            self.prevhour = now[3]
            if not self.status == self.button_state[now[3]][now[6]]:
                self._state(self.button_state[now[3]][now[6]])

    def pause(self):
        self.prevact = self.config.get("max_active_torrents")
        self.config.set("max_active_torrents", 0)
        self.core.apply_queue()

    def resume(self):
        self.config.set("max_active_torrents", self.prevact)
        self.core.apply_queue()

    def limit(self):
        self.config.set("max_download_speed", float(self.dllimit))
        self.config.set("max_upload_speed", float(self.ullimit))

    def unlimit(self):
        self.config.set("max_download_speed", float(self.dlmax))
        self.config.set("max_upload_speed", float(self.ulmax))

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

        dlmax_label = gtk.Label(_("High download limit:"))
        ulmax_label = gtk.Label(_("High upload limit:"))
        dllimit_label = gtk.Label(_("Low download limit:"))
        ullimit_label = gtk.Label(_("Low upload limit:"))

        #Select Widget
        drawing = scheduler_select(self.button_state_temp, hover_text, self.days)

        #boxes
        vbox_main = gtk.VBox()
        hbox_main = gtk.HBox()
        vbox_sub = gtk.VBox()
        hbox_key = gtk.HBox()
        hbox_info = gtk.HBox()
        # max boxen
        hbox_max = gtk.HBox()
        ebox_max = gtk.EventBox()
        ebox_max.add(hbox_max)
        ebrd_max = gtk.Frame()
        ebrd_max.add(ebox_max)
        ebrd_max.set_border_width(2)
        hbox_max.set_border_width(2)
        ebox_max.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#73D716"))
        ebrd_max.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#53B700"))
        # limit boxen
        hbox_limit = gtk.HBox()
        ebox_limit = gtk.EventBox()
        ebox_limit.add(hbox_limit)
        ebrd_limit = gtk.Frame()
        ebrd_limit.add(ebox_limit)
        ebrd_limit.set_border_width(2)
        hbox_limit.set_border_width(2)
        # Green
        # Yellow
        ebox_limit.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#EDD400"))
        ebrd_limit.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#CDB400"))

        #seperator
        sep = gtk.HSeparator()

        self._getglobals()
        # max spinbuttons
        dminput = gtk.SpinButton()
        dminput.set_numeric(True)    
        dminput.set_range(-1, 2048)
        dminput.set_increments(1, 10)
        dminput.set_value(float(self.dlmax))
        uminput = gtk.SpinButton()
        uminput.set_numeric(True)
        uminput.set_range(-1, 1024)
        uminput.set_increments(1, 10)
        uminput.set_value(float(self.ulmax))

        # limit spinbuttons
        dlinput = gtk.SpinButton()
        dlinput.set_numeric(True)    
        dlinput.set_range(-1, 2048)
        dlinput.set_increments(1, 10)
        dlinput.set_value(float(self.dllimit))
        ulinput = gtk.SpinButton()
        ulinput.set_numeric(True)
        ulinput.set_range(-1, 1024)
        ulinput.set_increments(1, 10)
        ulinput.set_value(float(self.ullimit))

        #pack
        dialog.vbox.pack_start(vbox_main)

        vbox_main.pack_start(hbox_main)
        vbox_main.pack_start(hover_text, False, True)
        vbox_main.pack_start(hbox_key, False, True)
        vbox_main.pack_start(hbox_info, False, True)
        vbox_main.pack_start(sep, False, True)
        vbox_main.pack_start(ebrd_max, False, True, 5)
        vbox_main.pack_start(ebrd_limit, False, True, 5)

        hbox_main.pack_start(vbox_sub, False, True, 5)
        hbox_main.pack_start(drawing)

        hbox_key.pack_start(gtk.Label(_("Green is the high limits, yellow is the low limits and red is stopped")), True, False)
        hbox_info.pack_start(gtk.Label(_("If a limit is set to -1, it is unlimitted.")), True, False)

        hbox_max.pack_start(dlmax_label, True, False)
        hbox_max.pack_start(dminput, True, False)
        hbox_max.pack_start(ulmax_label, True, False)
        hbox_max.pack_start(uminput, True, False)

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
            self.button_state = copy.deepcopy(drawing.button_state)
            self.dlmax = float(dminput.get_value())
            self.ulmax = float(uminput.get_value())

            self.dllimit = float(dlinput.get_value())
            self.ullimit = float(ulinput.get_value())

            now = time.localtime(time.time())
            self._state(self.button_state[now[3]][now[6]])

            writer = open(self.conf_file, "wb")
            pickle.dump([drawing.button_state,[self.dllimit, self.ullimit, self.dlmax, self.ulmax]], writer)
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
