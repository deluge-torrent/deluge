import deluge.pluginmanagerbase
pm = deluge.pluginmanagerbase.PluginManagerBase("core.conf", "deluge.plugin.core")

for p in pm.get_available_plugins():
    print "Plugin: %s" % (p)
    for k,v in pm.get_plugin_info(p).items():
        print "%s: %s" % (k, v)
