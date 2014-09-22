from __future__ import print_function

import deluge
from deluge.ui.client import aclient, sclient

from . import graph

sclient.set_core_uri()


def test_sync():
    if 1:
        upload = sclient.graph_get_upload()
        download = sclient.graph_get_download()
        print(upload)
        print(download)
    else:
        upload = [66804, 66915, 66974, 67447, 67540, 67318, 67320, 67249, 66659, 66489, 67027, 66914, 66802, 67303,
                  67654, 67643, 67763, 67528, 67523, 67431, 67214, 66939, 67316, 67020, 66881, 67103, 67377, 67141,
                  67366, 67492, 67375, 67203, 67056, 67010, 67029, 66741, 66695, 66868, 66805, 66264, 66249, 66317,
                  66459, 66306, 66681, 66954, 66662, 66278, 65921, 65695, 65681, 65942, 66000, 66140, 66424, 66480,
                  66257, 66271, 66145, 65854, 65568, 65268, 65112, 65050, 65027, 64676, 64655, 64178, 64386, 63979,
                  63271, 62746, 62337, 62297, 62496, 62902, 63801, 64121, 62957, 62921, 63051, 62644, 63240, 64107,
                  63968, 63987, 63644, 63263, 63153, 62999, 62843, 62777, 63101, 63078, 63178, 63126, 63401, 62630,
                  62451, 62505, 62254, 61485, 61264, 60937, 60568, 61011, 61109, 60325, 60196, 59640, 59619, 59514,
                  60813, 60572, 61632, 61689, 63365, 64583, 66396, 67179, 68209, 68295, 67674, 67559, 67195, 66178,
                  65632, 66124, 66456, 66676, 67183, 67620, 66960, 66347, 65925, 65907, 65896, 66738, 66703, 67060,
                  67004, 67007, 66329, 65304, 52002, 38969, 25433, 12426, 0, 0]
        download = [42926, 43853, 43157, 45470, 44254, 46272, 45083, 47344, 46716, 51963, 50112, 52334, 55525, 57545,
                    53691, 51637, 49574, 49836, 48295, 49843, 52878, 56014, 56966, 56938, 60065, 60461, 56542, 59526,
                    58678, 54424, 51862, 55109, 52132, 53783, 51687, 56567, 52182, 50758, 46714, 50511, 48161, 50920,
                    48694, 50528, 55074, 55420, 55882, 59268, 59958, 57938, 57115, 51424, 51180, 53184, 52879, 51177,
                    54417, 51097, 47901, 49870, 55865, 61118, 61476, 63498, 58878, 49630, 45975, 45632, 45892, 44855,
                    49495, 48304, 45829, 42152, 39403, 37574, 32384, 34933, 34901, 33492, 31953, 36271, 33826, 34515,
                    36408, 41106, 43054, 44110, 40810, 41383, 37267, 35881, 38660, 37525, 34857, 36718, 36842, 34281,
                    39528, 41854, 42952, 40021, 41722, 41045, 42917, 39287, 38672, 32824, 28765, 22686, 18490, 15714,
                    15268, 14793, 15305, 16354, 16720, 17502, 17857, 16622, 18447, 19929, 31138, 36965, 36158, 32795,
                    30445, 21997, 18100, 22491, 27227, 29317, 32436, 35700, 39140, 36258, 33697, 24751, 20354, 8211,
                    3836, 1560, 834, 2034, 1744, 1637, 1637, 1637, 0, 0]

    from .graph import NetworkGraph
    n = NetworkGraph()
    n.savedUpSpeeds = upload
    n.savedDownSpeeds = download

    n.draw(800, 200)
    n.surface.write_to_png('output_sync.png')


def test_async():
    g = graph.Graph()
    g.add_stat('download_rate', color=graph.green)
    g.add_stat('upload_rate', color=graph.blue)
    g.set_left_axis(formatter=deluge.common.fspeed, min=10240)
    g.async_request()
    aclient.force_call(True)
    surface = g.draw(600, 300)
    surface.write_to_png('output_async.png')


def test_dht():
    """'boring graph, but testing if it works'"""

    g = graph.Graph()
    g.add_stat('dht_nodes', color=graph.orange)
    g.add_stat('dht_cache_nodes', color=graph.blue)
    g.add_stat('dht_torrents', color=graph.green)
    g.add_stat('num_connections', color=graph.darkred)  # testing : non dht
    g.set_left_axis(formatter=str, min=10)
    g.async_request()
    aclient.force_call(True)
    surface = g.draw(600, 300)
    surface.write_to_png('output_dht.png')


def test_write():
    """
    writing to a file-like object; need this for webui.
    """
    class FakeFile:
        def __init__(self):
            self.data = []

        def write(self, str):
            self.data.append(str)

    g = graph.Graph()
    g.add_stat('download_rate', color=graph.green)
    g.add_stat('upload_rate', color=graph.blue)
    g.set_left_axis(formatter=deluge.common.fspeed, min=10240)
    g.async_request()
    aclient.force_call(True)
    surface = g.draw(900, 150)

    file_like = FakeFile()
    surface.write_to_png(file_like)
    data = "".join(file_like.data)

    f = open("file_like.png", "wb")
    f.write(data)
    f.close()

# test_sync()
test_async()
test_dht()
# test_write()
