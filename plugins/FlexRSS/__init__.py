FlexRSS_DEFAULTS = {
  'VERSION': (0, 2, 3)
}

plugin_name = "FlexRSS"
plugin_author = "Daddy"
plugin_version = "%d.%d.%d" % (FlexRSS_DEFAULTS['VERSION'][0], FlexRSS_DEFAULTS['VERSION'][1], FlexRSS_DEFAULTS['VERSION'][2])
plugin_description = _("""
Advanced RSS scraper

This plugin is similar in purpose to Mark Adamson's excellent RSS Broadcatcher, but targets a more advanced audience. It is extremely powerful, configurable, unforgiving, and difficult.

Filters use regular expressions with named patterns and strptime(3)-like format filters to match items.

For more information and documentation, visit http://dev.deluge-torrent.org/wiki/Plugins/FlexRSS""")

from FlexRSS.plugin import plugin_FlexRSS

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return plugin_FlexRSS(path, core, interface, FlexRSS_DEFAULTS)
