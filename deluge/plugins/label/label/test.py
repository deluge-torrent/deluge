from deluge.ui.client import sclient

sclient.set_core_uri()

print sclient.get_enabled_plugins()

#enable plugin.
if not "label" in sclient.get_enabled_plugins():
    sclient.enable_plugin("label")


#test labels.
print "#init labels"
try:
    sclient.label_remove("test")
except:
    pass
id = sclient.get_session_state()[0]

print "#add"
sclient.label_add("test")
print "#set"
sclient.label_set_torrent(id,"test")

print sclient.get_torrents_status({"label":"test"},"name")


print "#set options"
sclient.label_set_options("test",{"max_download_speed":999}, True)
print sclient.get_torrent_status(id, ["max_download_speed"]) , "999"
sclient.label_set_options("test",{"max_download_speed":9}, True)
print sclient.get_torrent_status(id, ["max_download_speed"]) , "9"
sclient.label_set_options("test",{"max_download_speed":888}, False)
print sclient.get_torrent_status(id, ["max_download_speed"]) , "9 (888)"

print sclient.get_torrent_status(id,['name', 'tracker_host', 'label'])





