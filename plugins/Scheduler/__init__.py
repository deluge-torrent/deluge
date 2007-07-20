# An example plugin for use with Deluge

plugin_name = _("Scheduler")            # The name of the plugin
plugin_author = "Lazka - updated by markybob"           # The author's Name
plugin_version = "0.5.2"                  # The plugin's version number
plugin_description = _("Scheduler")  # A description of the plugin

def deluge_init(deluge_path):
    global path
    path = deluge_path


from Scheduler.plugin import plugin_Scheduler

def enable(core, interface):
    global path
    return plugin_Scheduler(path, core, interface)
