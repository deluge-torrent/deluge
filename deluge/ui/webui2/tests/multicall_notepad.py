"""
test multicall.
"""
import time

from WebUi.webserver_common import ws, proxy, async_proxy
ws.init_06()

TORRENT_KEYS = ['name', 'total_size', 'num_files', 'num_pieces', 'piece_length',
    'eta', 'ratio', 'file_progress', 'distributed_copies', 'total_done',
    'total_uploaded', 'state', 'paused', 'progress', 'next_announce',
    'total_payload_download', 'total_payload_upload', 'download_payload_rate',
    'upload_payload_rate', 'num_peers', 'num_seeds', 'total_peers', 'total_seeds',
    'total_wanted', 'tracker', 'trackers', 'tracker_status', 'save_path',
    'files', 'file_priorities', 'compact', 'max_connections',
    'max_upload_slots', 'max_download_speed', 'prioritize_first_last', 'private'
    ]

if False:
    #
    #A: translate this into 1 multicall:

    start = time.time()
    stats = {
        'download_rate':proxy.get_download_rate(),
        'upload_rate':proxy.get_upload_rate(),
        'max_download':proxy.get_config_value('max_download_speed'),
        'max_upload':proxy.get_config_value('max_upload_speed'),
        'num_connections':proxy.get_num_connections(),
        'max_num_connections':proxy.get_config_value('max_connections_global')
    }

    print "sync-stats:",time.time() - start

    print stats

    #
    #map callback to a a dict-setter
    def dict_cb(key,d):
        def callback(result):
            d[key] = result
        return callback

    start = time.time()
    d = {}
    async_proxy.get_download_rate(dict_cb('download_rate',d))
    async_proxy.get_upload_rate(dict_cb('upload_rate',d))
    async_proxy.get_config_value(dict_cb('max_download',d),"max_download_speed")
    async_proxy.get_config_value(dict_cb('max_upload',d),"max_upload_speed")
    async_proxy.get_num_connections(dict_cb("num_connections",d))
    async_proxy.get_config_value(dict_cb('max_num_connections',d),"max_connections_global")

    async_proxy.force_call(block=True)

    print "Async-stats:",time.time() - start
    print d

    #
    #B: translate this to multicall:
    #

    #old-sync:
    start = time.time()

    torrent_list = [proxy.get_torrent_status(id, TORRENT_KEYS )
        for id in proxy.get_session_state()
        ]

    print "sync-list:",time.time() - start
    print torrent_list[0]

    #new async:
    """
                    torrent.compact,
                    torrent.max_connections,
                    torrent.max_upload_slots,
                    torrent.max_upload_speed,
                    torrent.max_download_speed,
                    torrent.prioritize_first_last,
                    torrent.private
    """


    start = time.time()

    torrent_ids  = proxy.get_session_state() #Syc-api.
    torrent_dict = {}
    for id in torrent_ids:
        async_proxy.get_torrent_status(dict_cb(id,torrent_dict), id, TORRENT_KEYS )
    async_proxy.force_call(block=True)

    print "Async-list:",time.time() - start
    print "\n".join(torrent_dict[torrent_ids[0]].keys())
    print torrent_dict[torrent_ids[0]]

if False:
    print proxy.get_config_value('download_location')

if True:
        torrent_id = proxy.get_session_state()[0]
        print torrent_id
        proxy.move_torrent([torrent_id],"/media/sdb1/test")