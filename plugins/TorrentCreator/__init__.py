

plugin_name = "Deluge Torrent Creator"
plugin_author = "regulate"
plugin_version = "0.1"
plugin_description = "A torrent creator plugin"

def deluge_init(deluge_path):
    global path
    path = deluge_path


from TorrentCreator.plugin import plugin_tcreator

def enable(core, interface):
    global path
    return plugin_tcreator(path, core, interface)
