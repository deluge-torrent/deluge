from deluge.ui.client import sclient, aclient
from deluge.common import fsize
sclient.set_core_uri()

totals = sclient.graph_get_totals()
print totals

for name, value in sclient.graph_get_totals().iteritems():
    print name , fsize(value)


print sclient.graph_get_stats("num_connections")["num_connections"]