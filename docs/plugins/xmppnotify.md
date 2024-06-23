# XMPP Notify Plugin

XMPP notify/control bot for Deluge 1.2.3

## Download
[XMPP Notify](http://bitbucket.org/enikesha/deluge-xmppnotify/downloads)

It requires twisted.words, twisted.names and [wokkel](http://wokkel.ik.nu/downloads) library to be installed.

## Features
* GTK and WebUI client interface
* Notify on torrent finish
* List current torrents
* Add torrents from URL

## Commands
* list -- Lists all current torrents
* down -- Lists downloading torrents
* up -- Lists uploading(seeding) torrents
* paused/queued -- Lists paused and queued torrents
* url <torrent url> [download location] -- Adds new torrent

## Configuration
Notifier jabber account/password: Pre-registered jabber account for bot.

Users to notify: Line separated list of accounts to notify for events.

PS. When installing via WebUI it's needed to restart 'deluged' and 'deluge-web' after enabling but before configuring plugin.

## Discussion/Support
[Ideas/Feature requests](http://bitbucket.org/enikesha/deluge-xmppnotify/issues/new)

[Deluge Forum Link](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=31245)

## Source Code
http://bitbucket.org/enikesha/deluge-xmppnotify/

