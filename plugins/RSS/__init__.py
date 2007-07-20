plugin_name = _("RSS Broadcatcher")
plugin_author = "Mark Adamson"
plugin_version = "1.0"
plugin_description = _("""
Download Torrents automatically from RSS Feeds

The latest version of my RSS autodownloader, which uses the Universal Feed parser (http://feedparser.org/). Add RSS feeds on the 'Feeds' tab, then add filters for TV shows (or whatever) on the 'Filters' tab. Double-click entries on the 'Torrents' tab to download extra torrents from the feeds. The Options are pretty self-explanatary.

Please message me (SatNav) on the forums and let me know how you get on..

Enjoy!""")


def deluge_init(deluge_path):
    global path
    path = deluge_path


from RSS.plugin import plugin_RSS

def enable(core, interface):
    global path
    return plugin_RSS(path, core, interface)
