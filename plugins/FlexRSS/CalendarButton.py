# Obviously needs work, but a decent start.
# Public domain

import gobject, gtk, time

class CalendarButton(gtk.Button):
    format = None
    calendar = None
    window = None

    __gsignals__ = {
        'date-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'date-selected': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
    }

    def __lost_focus(self, win, e):
        print e.type

    def __day_selected(self, calendar):
        self.window.hide()
        newdate = self.get_date()
        self.set_date(newdate[0], newdate[1], newdate[2])
        self.emit("date-selected", newdate)

    def __show_calendar(self, source):
        if self.window != None:
            self.window.show()
            return

        self.window = gtk.Window(gtk.WINDOW_POPUP)
        self.window.set_position(gtk.WIN_POS_MOUSE)
        self.window.set_destroy_with_parent(True)
        self.window.set_transient_for(source.get_ancestor(gtk.Window))
        self.window.add(self.calendar)
        self.window.show_all()

    def __set_date_on_button(self, year, month, day):
        self.set_label(time.strftime('%x', time.strptime('%d/%d/%d' % (day, month, year), '%d/%m/%Y')))

    def set_date(self, year, month, day):
        self.__set_date_on_button(year, month, day)
        self.calendar.select_month(month - 1, year)
        self.calendar.select_day(day)
        self.emit("date-changed", (year, month, day))

    def get_date(self):
        ret = self.calendar.get_date()
        return (ret[0], ret[1] + 1, ret[2])

    def __init__(self, year=None, month=None, day=None):
        value = time.localtime()

        if year == None:
            year = value[0]
        if month == None:
            month = value[1]
        if day == None:
            day = value[2]

        self.calendar = gtk.Calendar()
        self.calendar.select_month(month - 1, year)
        self.calendar.select_day(day)
        self.calendar.connect("day-selected-double-click", self.__day_selected)

        gtk.Button.__init__(self, time.strftime('%x', time.strptime('%d/%d/%d' % (day, month, year), '%d/%m/%Y')))

        self.connect("pressed", self.__show_calendar)
