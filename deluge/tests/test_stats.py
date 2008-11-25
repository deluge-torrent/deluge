#
# testing 123..
#

from deluge.ui.client import sclient
sclient.set_core_uri()
#/init

print "no-args:"
stats = sclient.get_stats()
for key in sorted(stats.keys()):
    print key, ":", stats[key]

