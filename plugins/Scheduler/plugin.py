import deluge.common, deluge.pref, gtk, copy, pickle, time
import os.path

class plugin_Scheduler:
    def __init__(self, path, deluge_core, deluge_interface):
        print "Found Scheduler plugin..."
        self.path = path
        self.core = deluge_core
        self.interface = deluge_interface

        self.days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.conf_file = os.path.join(deluge.common.CONFIG_DIR, "scheduler.conf")
        self.config = deluge.pref.Preferences()
        self.button_state_temp = [[0] * 7 for dummy in xrange(24)]
        self.status = -1

        #Load config
        self.button_state = None
        self.settings_structure = [["low_down", "max_download_speed", float], 
                                   ["low_up", "max_upload_speed", float], 
                                   ["high_down", "max_download_speed", float], 
                                   ["high_up", "max_upload_speed", float],
                                   ["low_activetorrents", "max_active_torrents", float],
                                   ["low_numslots", "max_upload_slots_global", float],
                                   ["low_maxconns", "max_connections_global", float],
                                   ["high_activetorrents", "max_active_torrents", float],
                                   ["high_numslots", "max_upload_slots_global", float],
                                   ["high_maxconns", "max_connections_global", float]]
                
        self.settings = {}
        
        try:
            reader = open(self.conf_file, "rb")
            data = pickle.load(reader)
            
            self.button_state = data[0]
            for i, item in enumerate(self.settings_structure):
                self.settings[item[0]] = data[1][i]

            reader.close()
        except:
            if self.button_state is None:
                self.button_state = [[0] * 7 for dummy in xrange(24)]
                
            for item in self.settings_structure:
                if item[0] not in self.settings:
                    temp = self.config.get(item[1])
                    
                    if item[2] is not None:
                        temp = item[2](temp)
                    
                    self.settings[item[0]] = temp

        now = time.localtime(time.time())
        self.status = self.button_state[now[3]][now[6]]
        self.prevhour = now[3]

        # Force speed changes when the plugin loads
        self._state(self.status)
    
    def unload(self):
        self.status = -1
        self.unlimit()

    def _state(self, state):
        if state == 0:
            self.unlimit()
        elif state == 1:
            self.limit()
        elif state == 2:
            self.pause()
        
        # Update the settings
        self.status = state

    def update(self):
        # Only do stuff if the status is valid
        if self.status < 0:
            return

        now = time.localtime(time.time())
        if now[3] != self.prevhour:
            self.prevhour = now[3]
            if not self.status == self.button_state[now[3]][now[6]]:
                self._state(self.button_state[now[3]][now[6]])

    def pause(self):
        self.config.set("max_active_torrents", 0)

    def limit(self):
        self.apply_configuration("low")

    def unlimit(self):
        self.apply_configuration("high")

    def apply_configuration(self, type):
        for item in self.settings_structure:
            if item[0].find(type) == 0:
                self.config.set(item[1], self.settings[item[0]])
        
        self.core.apply_queue()
        self.interface.apply_prefs()
    
    #Configuration dialog
    def configure(self, window):
        global scheduler_select

        self.button_state_temp = copy.deepcopy(self.button_state)
        
        #data
        spin = {}
        boxen = [
                 ["down", _("Download limit:"), -1, 2048], 
                 ["up", _("Upload limit:"), -1, 1024],
                 ["activetorrents", _("Active torrents:"), 0, 128],
                 ["numslots", _("Upload Slots:"), 0, 128],
                 ["maxconns", _("Max Connections:"), 0, 1024]]
        
        #dialog
        dialog = gtk.Dialog(_("Scheduler Settings"))
        dialog.set_default_size(600, 270)

        #buttons
        cancel_button = dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        ok_button = dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        
        #text
        hover_text = gtk.Label()

        #Select Widget
        drawing = scheduler_select(self.button_state_temp, hover_text, self.days)

        #boxes
        vbox_main = gtk.VBox()
        hbox_main = gtk.HBox()
        vbox_sub = gtk.VBox()
        hbox_key = gtk.HBox()
        hbox_info = gtk.HBox()
        hbox_settings = gtk.HBox()
        # high boxen
        tbl_high = gtk.Table(len(boxen), 2)
        ebox_high = gtk.EventBox()
        ebox_high.add(tbl_high)
        ebrd_high = gtk.Frame()
        ebrd_high.add(ebox_high)
        ebrd_high.set_border_width(2)
        tbl_high.set_border_width(2)
        ebox_high.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#73D716"))
        ebrd_high.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#53B700"))
        # low boxen
        tbl_low = gtk.Table(len(boxen), 2)
        ebox_low = gtk.EventBox()
        ebox_low.add(tbl_low)
        ebrd_low = gtk.Frame()
        ebrd_low.add(ebox_low)
        ebrd_low.set_border_width(2)
        tbl_low.set_border_width(2)
        # Green
        # Yellow
        ebox_low.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#EDD400"))
        ebrd_low.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#CDB400"))

        #seperator
        sep = gtk.HSeparator()
        
        #pack
        dialog.vbox.pack_start(vbox_main)

        vbox_main.pack_start(hbox_main)
        vbox_main.pack_start(hover_text, False, True)
        vbox_main.pack_start(hbox_key, False, True)
        vbox_main.pack_start(hbox_info, False, True)
        vbox_main.pack_start(sep, False, True)
        vbox_main.pack_start(hbox_settings)

        hbox_main.pack_start(vbox_sub, False, True, 5)
        hbox_main.pack_start(drawing)

        hbox_key.pack_start(gtk.Label(_("Green is the high limits, yellow is the low limits and red is stopped")), True, False)
        hbox_info.pack_start(gtk.Label(_("If a limit is set to -1, it is unlimitted.")), True, False)
        
        hbox_settings.pack_start(ebrd_high, True, True, 5)
        hbox_settings.pack_start(gtk.Label())
        hbox_settings.pack_start(ebrd_low, True, True, 5)
                     
        for box in [tbl_high, tbl_low]:
            for y, val in enumerate(boxen):
                if box is tbl_high: type = "high"
                else: type = "low"
                key = type + "_" + val[0]
                
                label = gtk.Label(val[1])
                label.set_alignment(0.0, 0.6)
                spin[key] = gtk.SpinButton()
                spin[key].set_numeric(True)    
                spin[key].set_range(val[2], val[3])
                spin[key].set_increments(1, 10)
                spin[key].set_value(self.settings[key])
                
                box.attach(label, 0, 1, y, y + 1)
                box.attach(spin[key], 1, 2, y, y + 1, False, False)

        for index in xrange(len(self.days)):
            vbox_sub.pack_start(gtk.Label(self.days[index]))

        #show
        dialog.show_all()

        #Save config    
        if dialog.run() == -5:
            # Detect changes to the config
            changed = False
            if not self.button_state == drawing.button_state:
                self.button_state = copy.deepcopy(drawing.button_state)
                changed = True
            
            for key in spin.keys():
                if not self.settings[key] == spin[key].get_value():
                    self.settings[key] = spin[key].get_value()
                    changed = True

            now = time.localtime(time.time())
            if changed:
                self._state(self.button_state[now[3]][now[6]])

            writer = open(self.conf_file, "wb")
            
            out = []
            
            for item in self.settings_structure:
                out.append(self.settings[item[0]])
                
            pickle.dump([drawing.button_state, out], writer)
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
