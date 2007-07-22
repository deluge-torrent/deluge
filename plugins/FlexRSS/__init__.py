
plugin_name = "FlexRSS"
plugin_author = "Daddy"
plugin_version = "0.0.1"
plugin_description = """
Advanced RSS scraper

This plugin is similar in purpose to Mark Adamson's excellent RSS Broadcatcher, but targets a more advanced audience. It is extremely powerful, configurable, unforgiving, and difficult.

Filters use regular expressions with named patterns and strptime(3)-like format filters to match items."""

from FlexRSS.plugin import plugin_FlexRSS

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return plugin_FlexRSS(path, core, interface)

FlexyRSS_DEFAULTS = {

}
