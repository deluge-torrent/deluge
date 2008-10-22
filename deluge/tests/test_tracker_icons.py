import time
import gobject
import os

from deluge.tracker_icons import TrackerIcons
from deluge.common import get_default_config_dir

def del_old():
    filename = os.path.join(get_default_config_dir("trackers"),"legaltorrents.com.ico")
    if os.path.exists(filename):
        os.remove(filename)

def test_get():
    #del_old()
    trackericons  = TrackerIcons()
    print trackericons.images
    print trackericons.get("unknown2")
    print trackericons.get("google.com")
    print trackericons.get("legaltorrents.com")
    time.sleep(5.0)
    print trackericons.get("legaltorrents.com")

def callback1(value):
    print "callback1:", value
    return False

def test_async():
    #test is broken :(,. but filtertreeview works.
    del_old()
    trackericons  = TrackerIcons()
    trackericons.get_async("legaltorrents.com",callback1)
    print "here"
    gobject.MainLoop()



test_get()
#test_async()


