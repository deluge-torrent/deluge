#
# moving and refactoring torrent-filtering from labels-plugin to core.
#

#init:
from deluge.ui.client import sclient
sclient.set_core_uri()
torrent_id = sclient.get_session_state()[0]
print torrent_id
#/init


#get_status_keys
#both lines should return the same if all plugins are disabled.
#the 1st should be longer if the label plugin is enabled.
print sorted(sclient.get_torrent_status(torrent_id,[]).keys())
print sorted(sclient.get_status_keys())


#filters on default state fields
print sclient.get_status(["name","state"], {"state":"Paused"})
print sclient.get_status(["name","state"], {"tracker_host":"aelitis.com"})

#plugin status fields:
print sclient.get_status(["name","state"], {"label":"test"})

#special filters:
print sclient.get_status(["name","state"], {"keyword":"az"})







