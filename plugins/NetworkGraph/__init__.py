plugin_name = _("Network Activity Graph")
plugin_author = "Alon Zakai, Zach Tibbitts"
plugin_version = "0.2"
plugin_description = _("Network Activity Graph plugin\n\nWritten by Kripkenstein")


def deluge_init(deluge_path):
    global path
    path = deluge_path

from NetworkGraph.plugin import plugin_NetGraph

def enable(core, interface):
    global path
    return plugin_NetGraph(path, core, interface)
