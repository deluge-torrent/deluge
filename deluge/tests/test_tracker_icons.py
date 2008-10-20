from deluge.tracker_icons import TrackerIcons

def test():
    trackericons  = TrackerIcons()

    print trackericons._fetch_icon("unknown?") #exception, Returns None
    print trackericons._fetch_icon("deluge-torrent.org") #404 , returns False
    print trackericons._fetch_icon("legaltorrents.com")
    print trackericons.get("thepiratebay.com")
    print trackericons.get("unknown2") #exception, returns None
    print trackericons.get("legaltorrents.com") #logs cached
    print trackericons.get("google.com")


test()
