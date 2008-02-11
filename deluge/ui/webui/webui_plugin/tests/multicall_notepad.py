"""
test multicall.
"""
import time

from WebUi.webserver_common import ws
ws.init_06()
async_proxy = ws.async_proxy



#
#A: translate this into 1 multicall:

start = time.time()
stats = {
    'download_rate':ws.proxy.get_download_rate(),
    'upload_rate':ws.proxy.get_upload_rate(),
    'max_download':ws.proxy.get_config_value('max_download_speed'),
    'max_upload':ws.proxy.get_config_value('max_upload_speed'),
    'num_connections':ws.proxy.get_num_connections(),
    'max_num_connections':ws.proxy.get_config_value('max_connections_global')
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

torrent_list = [ws.proxy.get_torrent_status(id,[])
    for id in ws.proxy.get_session_state()
    ]

print "sync-list:",time.time() - start
print torrent_list

#new async:

start = time.time()

torrent_ids  = ws.proxy.get_session_state() #Syc-api.
torrent_dict = {}
for id in torrent_ids:
    async_proxy.get_torrent_status(dict_cb(id,torrent_dict), id, ["name"])
async_proxy.force_call(block=True)

print "Async-list:",time.time() - start
print torrent_dict[torrent_ids[0]].keys()
print torrent_dict[torrent_ids[0]]["name"]












