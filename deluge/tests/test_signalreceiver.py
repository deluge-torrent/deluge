from deluge.configmanager import ConfigManager
import deluge.xmlrpclib as xmlrpclib

config = ConfigManager("gtkui.conf")

client = xmlrpclib.ServerProxy("http://localhost:" + str(config["signal_port"]))

client.emit_signal("torrent_finished", "abc123")

