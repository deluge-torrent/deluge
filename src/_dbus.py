# Import all we will use in deluge
from dbus import Interface, SessionBus, version

# Code for dbus_importing borrowed from Listen (http://listen-project.org)
# I couldn't figure out how to use dbus without breaking on versions past
# 0.80.0.  I finally found a solution by reading the source code from the
# Listen project. 
if version >= (0,41,0) and version < (0,80,0):
    import dbus.glib
elif version >= (0,80,0):
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)
