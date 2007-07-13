# A simple plugin to display Hello, World

plugin_name = "Hello World"
plugin_author = "Zach Tibbitts"
plugin_version = "1.0"
plugin_description = 'Displays "Hello, World"'

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return plugin_Hello(path, core, interface)


class plugin_Hello:
    def __init__(self, path, deluge_core, deluge_interface):
        self.path = path
        self.core = deluge_core
        self.interface = deluge_interface
    
    def unload(self):
        pass
    
    def update(self):
        print "Hello, World!"


