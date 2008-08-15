#
# moving and refactoring torrent-filtering from labels-plugin to core.
#

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

#default, no filter argument.
print sclient.get_dev_torrents_status(None, ["name","state"])

print "HI! , after this the errors start"

#torrent_id filters and list-arguments:
print sclient.get_dev_torrents_status({"id":torrent_id}, ["name","state"])
print sclient.get_dev_torrents_status({"id":[torrent_id, torrent_id2]}, ["name","state"])

#filters on default state fields
print sclient.get_dev_torrents_status({"state":"Paused"}, ["name","state"])
print sclient.get_dev_torrents_status({"state":["Paused","Downloading"]}, ["name","state"])
print sclient.get_dev_torrents_status({"tracker_host":"aelitis.com"}, ["name","state"])


#plugin status fields:
print sclient.get_dev_torrents_status({"label":"test"}, ["name","state"])
print sclient.get_dev_torrents_status({"label":["test","tpb"]}, ["name","state"])

#special filters:
print sclient.get_dev_torrents_status({"keyword":"az"}, ["name","state"])







