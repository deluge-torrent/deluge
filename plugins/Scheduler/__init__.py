
# The name of the plugin
plugin_name = "Scheduler"
# The author's Name
plugin_author = "Lazka - updated by markybob and man_in_shack"
# The plugin's version number
plugin_version = "0.5.6.1"
# A description of the plugin
plugin_description = "Scheduler"

def deluge_init(deluge_path):
    global path
    path = deluge_path

from Scheduler.plugin import plugin_Scheduler

def enable(core, interface):
    global path
    return plugin_Scheduler(path, core, interface)
