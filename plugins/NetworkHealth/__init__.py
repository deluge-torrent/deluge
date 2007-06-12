

plugin_name = "Network Health Monitor"
plugin_author = "Alon Zakai, Zach Tibbitts"
plugin_version = "0.2"
plugin_description = "Network Health Monitor plugin\n\nWritten by Kripkenstein"


def deluge_init(deluge_path):
    global path
    path = deluge_path


from NetworkHealth.plugin import plugin_NetworkHealth

def enable(core, interface):
    global path
    return plugin_NetworkHealth(path, core, interface)
