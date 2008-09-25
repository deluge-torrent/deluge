#
# moving and refactoring torrent-filtering from labels-plugin to core.
#

from deluge.ui.client import sclient
sclient.set_core_uri()
#/init

print "no-args:"
print sclient.get_statusbar()

print "include-defaults:"
print sclient.get_statusbar(True)

print "no-defaults:"
print sclient.get_statusbar(False)

