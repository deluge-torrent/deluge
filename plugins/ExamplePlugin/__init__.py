# An example plugin for use with Deluge

plugin_name = "Example Plugin"            # The name of the plugin
plugin_author = "Zach Tibbitts"           # The author's Name
plugin_version = "0.5.0"                  # The plugin's version number
plugin_description = "An example plugin"  # A description of the plugin

def deluge_init(deluge_path):
    global path
    path = deluge_path


from ExamplePlugin.plugin import plugin_Example

def enable(core, interface):
    global path
    return plugin_Example(path, core, interface)
