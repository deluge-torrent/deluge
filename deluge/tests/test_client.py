#------------------------------------------------------------------------------
#tests:
#------------------------------------------------------------------------------

from deluge.ui.client import aclient, sclient

def test_introspection():
    print("*start introspection test*")
    sclient.set_core_uri()
    print("list_methods", sclient.list_methods())
    print("sig of block_ip_range", sclient.methodSignature('block_ip_range'))
    print("doc of block_ip_range",  sclient.methodHelp('block_ip_range'))

def test_sync():
    print("*start sync test*")
    sclient.set_core_uri()

    #get list of torrents and display the 1st.
    torrent_ids = sclient.get_session_state()
    print("session_state():", torrent_ids)
    print("get_torrent_status(%s):" %  torrent_ids[0],
        sclient.get_torrent_status(torrent_ids[0], []))

    sclient.pause_torrent(torrent_ids)

    print("paused:", [
        sclient.get_torrent_status(id, ['paused'])['paused']
        for id in torrent_ids])

    sclient.resume_torrent(torrent_ids)
    print("resumed:", [
        sclient.get_torrent_status(id, ['paused'])['paused']
        for id in torrent_ids])

def test_async():
    print("*start async test*")
    torrent_ids = []

    #callbacks:
    def cb_session_state(temp_torrent_list):
        print("session_state:" , temp_torrent_list)
        torrent_ids.extend(temp_torrent_list)

    def cb_torrent_status_full(status):
        print("\ntorrent_status_full=", status)

    def cb_torrent_status_paused(torrent_state):
        print("paused=%s" % torrent_state['paused'])

    #/callbacks

    aclient.set_core_uri()
    aclient.get_session_state(cb_session_state)

    print("force_call 1")
    aclient.force_call(block=True)
    print("end force_call 1:", len(torrent_ids))


    #has_callback+multicall
    aclient.pause_torrent(torrent_ids)
    aclient.force_call(block=True)
    for id in torrent_ids:
        aclient.get_torrent_status(cb_torrent_status_paused, id , ['paused'])

    aclient.get_torrent_status(cb_torrent_status_full, torrent_ids[0], [])

    print("force_call 2")
    aclient.force_call(block=True)
    print("end force-call 2")



    print("resume:")
    aclient.resume_torrent(torrent_ids)
    for id in torrent_ids:
        aclient.get_torrent_status(cb_torrent_status_paused, id , ['paused'])

    aclient.force_call(block=True)

test_introspection()
test_sync()
test_async()
