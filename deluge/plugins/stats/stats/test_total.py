from deluge.ui.client import sclient, aclient
from deluge.common import fsize
sclient.set_core_uri()

def print_totals(totals):
    for name, value in totals.iteritems():
        print name , fsize(value)

    print "overhead:"
    print "up:", fsize(totals["total_upload"]  - totals["total_payload_upload"] )
    print "down:", fsize(totals["total_download"]  - totals["total_payload_download"] )


print "==totals=="
print_totals(sclient.stats_get_totals())

print "==session totals=="
print_totals(sclient.stats_get_session_totals())
