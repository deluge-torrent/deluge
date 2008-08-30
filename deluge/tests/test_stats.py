from deluge.ui.client import sclient
sclient.set_core_uri()

for key, val in sclient.get_stats().iteritems():
    print "%s:%s" % (key,val)