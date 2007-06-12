
plugin_name = "Torrent Search"
plugin_author = "Zach Tibbitts"
plugin_version = "0.5"
plugin_description = "A searchbar for torrent search engines"


def deluge_init(deluge_path):
    global path
    path = deluge_path


from TorrentSearch.plugin import plugin_Search

def enable(core, interface):
    global path
    return plugin_Search(path, core, interface)
