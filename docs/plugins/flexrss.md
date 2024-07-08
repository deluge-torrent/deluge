# FlexRSS

This plugin is only compatible with the **0.5.x** and **1.1.x** releases of deluge.

Note: For **1.2.x** or newer releases see [FlexGet](/plugins/flexget.md) or [yarss2](/plugins/yarss2.md).

## Overview

FlexRSS is a Deluge plugin for automatically handling RSS feeds. It is designed for advanced users, and makes few sacrifices of power and flexibility to ease of use. If you are already familiar with regular expressions, you should feel right at home.

Less technical users will likely want to use the "Simple RSS" plugin that is included with Deluge, which is far easier to use.

## Feeds

The feeds tab is fairly easy to use. One thing you should remember when choosing your feeds is that the feed should link directly to the torrent file, not to a detials page. Two popular examples of RSS feeds not conforming to this requirement are Demonoid and Mininova, though the latter does provide a direct feeds (by appending "?direct" to the URL)—they just don't make them easy to find.

If you expand a feed and right click on a single item, there is an option to "create filter", which will cause FlexRSS to create a new filter and take its best guess as to how to configure the new filter. This works well for items using standard formats.

## Configuration

### Interface

The interface section currently contains a singe option: "Show button on toolbar", which will add a button for FlexRSS in the Deluge toolbar. Depending on how heavily you rely on the plugin, you may or may not think cluttering up Deluge's interface is worth it.
Feed Retrieval

This section also contains a single option, one that will hopefully become obsolete soon. By default, FlexRSS retrieves feeds from the default thread, which blocks the entire interface. This behaviour is, obviously, not proper. That said, the threading support I tried to add doesn't seem very reliable, so I made it optional and disabled it by default. If anybody is interested in fixing this, it would be much appreciated.

### Cookies

The "Configuration" tab contains an area where you can enter cookies for FlexRSS to send whenever it requests data from them (either polling feeds or downloading a torrent). These cookies are stored in a Netscape-style, and probably the easiest way to use cookies with FlexRSS is to simply copy a cookies.dat file from a browser like Firefox to ~/.config/deluge/flexrss-cookies.dat.

## Filters

The filters tab is where all the work takes place. and where all of the documentation takes place. Crap.

### Information

This section is where you specify basic information about the feed—specifically, the name of the filter, the type of the filter, and which feed(s) you want to test the filter against. The filter type is one of:

 Generic::
   Generic filters are the most simple type, but also probably the least often used. Their concept of history is fairly naive—they merely record the URI of all the items they have matched. This means that it is quite possible to download the same item more than once.
 TV Show::
   TV show filters are probably the most often used type of filter. They record a season and episode number for each match, meaning that they allow you to only download items you haven't yet downloaded. Season defaults to 0, so for things like anime where shows generally don't include a season, history is based on episode number alone.
 TV Show (dated)::
   The third and final type of filter is for items which use dates instead of the more common season/episode numbering.

### Patterns

Patterns are the heart of FlexRSS. They are case-insensitive regular expressions with named patterns representing episode numbers. For details of regular expressions in Python, you can consult the [Python manual section on Regular Expression Syntax](http://docs.python.org/lib/re-syntax.html), or, for a more gentle Python-specific introduction, the [Python Regular Expression HOWTO](http://www.amk.ca/python/howto/regex/). The rest of this section will assume that you are familiar with regular expressions.

The named patterns you should define differ based on what type of filter you are using. TV shows use 's' and 'e', which represent 'season' (or 'series' if you prefer en_GB) and 'episode', respectively. Dated TV shows use 'Y', 'y', 'm', and 'd', for 4-digit year, 2-digit year, month, and day. Each named pattern also has an alias which can be used for convenience and work most situations—here is a list of these patterns and what they compile to:

 %s::
   (?P<s>![0-9]+)
 %e::
   (?P<e>![0-9]+)
 %Y::
   (?P<Y>![0-9]{4})
 %y::
   (?P<y>![0-9]{2})
 %m::
   (?P<m>![0-9]{1,2})
 %d::
   (?P<d>![0-9]{1,2})

It is worth noting that all of these named patterns should match only substrigs representing integers. Any named pattern can be omitted, but will default to 0, so if you don't include any only the first item will be downloaded.

So, for instance, "show.s%se%e" will be converted into "show.s(?P<s>![0-9]+)e(?P<e>![0-9]+)" before it is run. This is the full extent of the preprocessing done before running the regex, which means that you must escape any special characters that you want treated as literals.

Sometimes these shortcuts are not enough to properly represent a filter, and you must use the more verbose version. However, it is possible to mix the two. For example, "My Favourite Show 108" could be the 108th episode of "My Favourite Show", or it could be the 8th episode of season 1 (I encounter both in the wild). To make sure you get what you want, you can use the filter "my.favourite.show.%s(?P<e>![0-9]{2})"

Patterns can test against either the title or the link. You can add as many patterns as you want to a single filter, and the filter will be considered a match if ANY of them match.

### History Restriction

With non-generic filters, you can use history restriction to further limit what content is downloaded. Simply specify a either a starting episode, ending episode, or both.

### Download

Several things in the interface could be more appropriately named, but I think this section takes the cake. Basically, it is a group of miscellaneous options that I thought would be nice to have.

 Insert torrent at top of queue.::
   The default behaviour is to insert new torrents at after currenly downloading torrents. If you're really into something and want to make sure you get it as soon as possible, you can use this option to make sure torrents are sent to the top of the queue.
 Set state to paused.::
   This one is nice if you're not overly confident about your pattern-fu. Torrents are retrieved, but paused immediately so they will not download without further intervention.
 Delete filter when matched.::
   Want to throw away a filter after it has matched? Check the box.

### Link Rewriting

Earlier, I mentioned that some sites link to a details page instead of the actual torrent. If the URI of the torrent is easily predictable from the URI of the detials page, you can use link rewriting to "fix" it.

Link rewriting uses regular expressions as well. For on overview on how to use it, see the [Python re::sub documentation](http://docs.python.org/lib/node46.html#l2h-405), or a more friendly explanation in the [Search and Replace section of the Python Regular Expression HOWTO](http://www.amk.ca/python/howto/regex/regex.html#SECTION000620000000000000000).

### Output

Output just lets you specify where to save your torrent to.

## Download

**FlexRSS for 0.5.x**
 You can download the latest version of FlexRSS from the [FlexRSS plugin](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=219) thread in the Deluge forums.
**FlexRSS for 1.x**
 A port of FlexRSS for the 1.x series is available in the forums: https://forum.deluge-torrent.org/viewtopic.php?f=9&t=10185