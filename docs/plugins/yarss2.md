# YaRSS2

An RSS plugin for Deluge configured through the GTK client.

## Current features

* RSS Feeds with individual update times.
* Cookie support
* Magnet link support
* Sending emails on torrent(s) added, with the list of torrents in the message.
* Multiple (email message) notifications can be created and applied to different subscriptions.
* Search using regex, one field for inclusion and one for exclusion.
* "Move completed", "Download location" and "Add Paused" options.
* Support for labeling torrents with the Label plugin.
* Log window containing info on what is going on.
* It runs on the daemon, so it will work well in a daemon/thin client setup.

Features that hopefully will be implement:

* Smart episodes filtering including history to avoid the same episodes being added multiple times.
* Command line client
* Better search, maybe a helper to create regex filters.

### Deluge version support

For Deluge v1.3.X, use YaRRS2 v1.X

Tested with Deluge 1.3.5 on:
* Windows XP
* Ubuntu 14.04
* FreeBSD 10 (daemon)

For Deluge v2.X use YaRSS2 v2.X

Tested with Deluge 2.0.3 on:
* Ubuntu 18.04


## Links

### [Download](https://bitbucket.org/bendikro/deluge-yarss-plugin/downloads)
### [Changelog](https://bitbucket.org/bendikro/deluge-yarss-plugin/src/master/CHANGELOG.md)
### [Forum thread](http://forum.deluge-torrent.org/viewtopic.php?t=39551) (if you need help)

## Getting started

### Download

Download YaRSS2 from the [bitbucket repo](https://bitbucket.org/bendikro/deluge-yarss-plugin/downloads).

You must download the egg that matches your python version (e.g. py3.6.egg for python 3.6). See [http://dev.deluge-torrent.org/wiki/Plugins#InstallingPlugins](http://dev.deluge-torrent.org/wiki/Plugins#InstallingPlugins) for details if you are unsure.

### Installing the plugin

The plugin egg file can be installed through the Deluge GTK client, or it can be installed manually.

See [instructions for how to install](http://dev.deluge-torrent.org/wiki/Plugins#InstallingPlugins)

If you run Deluge in non-Classic mode (daemon and client setup), take a look at [Running a server/seedbox with a Deluge daemon](http://dev.deluge-torrent.org/wiki/Plugins/YaRSS2#RunningaserverseedboxwithaDelugedaemon)
### RSS feed

Start by registering a RSS feed in the tab "RSS Feeds". Make sure the links link to torrent files, and not a new HTML page.
The "Update time" is how often this feed is checked. It depends on how often the feeds are updated, but usually, between 60-120 minutes should suffice. The minimum value is 5 minutes, to avoid overloading the server.

### Subscription
Subscriptions define the content you want to download from an RSS feed.
The search is regex based, which enables extremely powerful search expressions. However, it's not always straight forward to define right.

To help you verify the expression, the list of the current torrents in the RSS feed will show if the torrent matches, and which part of the title that matches

Regex hints:
|     |       |
|-----|-------|
|Regex|Comment|
|.|Any character|
|*|Zero or more of the previous expression|
|+|One or more of the previous expression|
|.*|Zero or more of any character|
|\d|Any number 0-9 (Only one character)|
|\d+|One or more numbers|
|\d!{2}|Exactly two numbers|
|\d{1,2}|One or two numbers|
|(720p|1080p)| **720p** or **1080p**|

Example
* Title1: "My Favourite Series some-random-characters.720p.GROUP"
* Title2: "My.Favourite.Series.some-random-characters.1080p.GROUP"
* Title3: "My.Favourite.Series.S1E04.1080p.GROUP"
* Title4: "My.Favourite.Series.S1E1.1080p.GROUP"

|     |      |
|-----|------|
|Regex|Matche|
|My Favourite Series| Title1|
|My.Favourite.Series| all|
|.| all|
|My.Favourite.Series.*720p| Title1|
|My.Favourite.Series.*(720p|1080p)| All|
|My.Favourite.Series.S01E\d!{2}*1080p| Title3 (as well as any episode 00-99)|
|My.Favourite.Series.S01E\d{1,2}.*1080p| Title3 and Title4|

## Troubleshooting
### No torrents appear in the list when creating a new subscription

If no torrents appear in the list in the subscription dialog, but they show up fine in your web browser, the problem is likely that the web server requires some cookies. The cookies are added automatically by the browser, but you'll have to add them manually to YaRSS2.
There are a lot of guides on how to find the correct cookie values (most torrent sites that require cookies have some guide or forum thread where this is explained).

1. Find the necessary cookie values for your tracker in your web browser.
2. Go to the settings tab in YaRSS2 in the preferences and click the cookies tab at the bottom.
3. Provide the base URL of the tracker in the "Site URL" field. If the address is *www.address.com/rss+23423r/whatever++*, use only *www.address.com*
4. Add each value/pair as they are stored in your browser.
5. Save the cookies and test if this works in the subscription dialog.

<img src="Plugins YaRSS2/YaRSS_cookies.2012-09-12.png" width=400px>

The *pass* and *uid* keys are just examples, and might be named differently on your tracker.

### Dealing with feeds that are missing a pubDate tag

Some trackers publish RSS feeds that do not have the standard pubDate tag for each item that contains the timestamp of when the item was added to the feed.  Without this tag, YaRSS2 cannot process the feed, as it has no way of knowing a new item from an old one.  Most of these trackers DO include a timestamp somewhere in each item's entry, but if it's not in the pubDate tag, then YaRSS2 doesn't find it.  To solve this, you can contact the feed's publisher and request that they conform to the RSS standard and include the pubDate tag in their feed.  When they tell you to go pound sand, fear not.  There is a workaround that's fairly easy.  To add the pubDate tag into an existing RSS feed yourself, you can use a service from Yahoo called Pipes:

[http://pipes.yahoo.com/pipes/](http://pipes.yahoo.com/pipes/)

Yahoo has pretty good documentation for this tool, so you should be able to figure out the Pipes tool after a little experimenting.  Here's a general guideline of how to add the missing pubDate tag:

* Open the RSS feed in a web browser and view the page's source. You'll see all the tags for each item. Identify the tag that contains the published date.
* Create a Yahoo account and build a new pipe. String the following modules together in the following order.
* Use the fetch feed module to read the source feed.
* Then use the rename module to copy the tag containing the date into a new tag called pubDate.
* You may need to use the regex module to strip all but the time and date out of your new pubDate tag.
* Use the Create RSS module to map the tags to conform to RSS standard.
* Save and run the pipe. Click on "get as RSS" and use the link it generates as your RSS source in YaRSS2.
* Enjoy.  The feed now has a proper timestamp tag and should work.

Hopefully this will help some people get their favourite feeds working with YaRSS2.

### Email notifications

You can send a test email to see if your email settings works.
In a thin client/daemon setup, the test email is sent from the client machine, but the real emails sent by YaRSS2 when adding torrents are sent from the daemon, so if you have problems sending emails it might be caused by issues on your server.

For gmail, the following settings works:
|               |                  |
|---------------|------------------|
|**SMTP server**|**smtp.gmail.com**|
|**Port**|**587**|
|**From email address**|**name @ gmail.com**|
|**Username**|**same as your email address**|
|**Password**|**app password**|

To send emails with gmail, you must create an app password for authentication. Using your account password is reported to cause problems. See
https://support.google.com/accounts/answer/185833?hl=en

## Running a server/seedbox with a Deluge daemon

If you have a server/seedbox you need to verify that the python version on the server corresponds to the version of the plugin egg you installed.

See [section about Client-Server Setups](http://dev.deluge-torrent.org/wiki/Plugins#Client-ServerSetups)

After installing, restart both the daemon and the client and YaRSS2 should now be available in the list of plugins.
