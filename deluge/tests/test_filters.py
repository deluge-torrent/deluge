#
# moving and refactoring torrent-filtering from labels-plugin to core.
#

KEYS = ["name","state", "label"]
#init:
from deluge.ui.client import sclient
sclient.set_core_uri()
torrent_id = sclient.get_session_state()[0]
torrent_id2 = sclient.get_session_state()[1]
print torrent_id
#/init


#get_status_keys
#both lines should return the same if all plugins are disabled.
#the 1st should be longer if the label plugin is enabled.
print sorted(sclient.get_torrent_status(torrent_id,[]).keys())
print sorted(sclient.get_status_keys())

print "#default, no filter argument."
print sclient.get_torrents_status(None, KEYS)



print "#torrent_id filter:"
print sclient.get_torrents_status({"id":[torrent_id, torrent_id2]}, KEYS)


print "#filters on default status fields:"
#print sclient.get_torrents_status({"state":"Paused"}, KEYS)
print sclient.get_torrents_status({"state":["Paused","Downloading"]}, KEYS)
print sclient.get_torrents_status({"tracker_host":["aelitis.com"]}, KEYS)



print "#status fields from plugins:"
#print sclient.get_torrents_status({"label":"test"}, KEYS)
print sclient.get_torrents_status({"label":["test","tpb"]}, KEYS)


print "#special filters (ERRORS START HERE!):"
print sclient.get_torrents_status({"keyword":"az"}, KEYS)
print sclient.get_torrents_status({"state":"Active"}, KEYS)
