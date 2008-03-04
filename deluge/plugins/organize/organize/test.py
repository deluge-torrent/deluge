from deluge.ui.client import sclient

sclient.set_core_uri()

ids = sclient.get_session_state()

for t in sclient.get_torrents_status(ids, ['name','tracker_name','tracker']).itervalues():
    print t

for tracker,count in sclient.organize_tracker_filter_items():
    print tracker, count

for state,count in sclient.organize_state_filter_items():
    print state, count

print sclient.organize_all_filter_items()


print 'tracker.aelitis.com:'
print sclient.organize_get_session_state({'tracker':'tracker.aelitis.com'} )

print 'no results'
print sclient.organize_get_session_state({'tracker':'no results'} )


print 'seeding'
print sclient.organize_get_session_state({'state':'Seeding'} )

print 'paused'
print sclient.organize_get_session_state({'state':'Paused'} )

print 'seeding+tracker.aelitis.com'
print sclient.organize_get_session_state({
    'tracker':'tracker.aelitis.com',
    'state':'Seeding'})

print 'on keyword:'
print sclient.organize_get_session_state({'keyword':'client'})

print 'on keyword:no results'
print sclient.organize_get_session_state({'keyword':'lasjhdinewhjdeg'})
