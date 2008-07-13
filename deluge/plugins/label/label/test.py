from deluge.ui.client import sclient

sclient.set_core_uri()

print sclient.get_enabled_plugins()

#enable plugin.
if not "label" in sclient.get_enabled_plugins():
    sclient.enable_plugin("label")

#test filter items.
print "# label_filter_items()"
for cat,filters in  sclient.label_filter_items():
    print "-- %s --" % cat
    for filter in filters:
        print "  * %s (%s)" % (filter[0],filter[1])

# test filtering
print "#len(sclient.label_get_filtered_ids({'tracker':'tracker.aelitis.com'} ))"
print len(sclient.label_get_filtered_ids({'tracker':'tracker.aelitis.com'} ))

print "#len(sclient.label_get_filtered_ids({'state':'Paused'} ))"
print len(sclient.label_get_filtered_ids({'state':'Paused'} ))


print "#len(sclient.label_get_filtered_ids({'keyword':'az'} ))"
print len(sclient.label_get_filtered_ids({'keyword':'az'} ))


print "#len(sclient.label_get_filtered_ids({'state':'Paused','tracker':'tracker.aelitis.com'} ))"
print len(sclient.label_get_filtered_ids({'state':'Paused','tracker':'tracker.aelitis.com'} ))

print "#test status-fields:"
ids = sclient.get_session_state()

torrents = sclient.get_torrents_status(ids,['name', 'tracker_host', 'label'])

for id,torrent in torrents.iteritems():
    print id, torrent

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

print "#len(sclient.label_get_filtered_ids({'label':'test'} ))"
print len(sclient.label_get_filtered_ids({'label':'test'} ))

#test filter items.
print "# label_filter_items()"
for cat,filters in  sclient.label_filter_items():
    if cat == "label":
        print "-- %s --" % cat
        for filter in filters:
            print "  * %s (%s)" % (filter[0],filter[1])


print "#set options"
sclient.label_set_options("test",{"max_download_speed":999}, True)
print sclient.get_torrent_status(id, ["max_download_speed"]) , "999"
sclient.label_set_options("test",{"max_download_speed":9}, True)
print sclient.get_torrent_status(id, ["max_download_speed"]) , "9"
sclient.label_set_options("test",{"max_download_speed":888}, False)
print sclient.get_torrent_status(id, ["max_download_speed"]) , "9 (888)"

print sclient.get_torrent_status(id,['name', 'tracker_host', 'label'])





