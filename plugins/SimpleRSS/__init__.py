plugin_name = _("Simple RSS")
plugin_author = "Mark Adamson"
plugin_version = "1.0"
plugin_description = _("""
Download Torrents automatically from SimpleRSS Feeds

Add RSS feeds on the 'Feeds' tab, then add filters for TV shows (or whatever) on the 'Filters' tab. Double-click entries on the 'Torrents' tab to download extra torrents from the feeds. The Options are pretty self-explanatary.

Please message me (SatNav) on the forums and let me know how you get on..

Enjoy!""")


def deluge_init(deluge_path):
    global path
    path = deluge_path


from SimpleRSS.plugin import plugin_SimpleRSS

def enable(core, interface):
    global path
    return plugin_SimpleRSS(path, core, interface)
