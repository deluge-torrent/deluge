# [IfaceWatch](/ifacewatch)

Watch for IP changes on specific interfaces and notify libtorrent.

## Current features

* No WebUI support
* Works only on Unix based hosts (limitation of [PyIface](https://github.com/bat-serjo/PyIface))
* It runs on the daemon, so it will work well in a daemon/thin client setup.

## Links

* [Download](https://github.com/bendikro/deluge-iface-watch/releases)
* [Changelog](https://github.com/bendikro/deluge-iface-watch#changelog)
* [Forum thread](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=52739)

## Getting started

### Download

Download [IfaceWatch](/ifacewatch) from the [https://github.com/bendikro/deluge-iface-watch/releases](https://github.com/bendikro/deluge-iface/watch/releases).

You must download the egg that matches your python version (Python 2.6 or 2.7). See [http://dev.deluge-torrent.org/wiki/Plugins#InstallingPlugins](http://dev.deluge-torrent.org/wiki/Plugins#InstallingPlugins) for details if you are unsure.

### Installing the plugin

The plugin egg file can be installed through the Deluge GTKUI, or it can be installed manually.

See [instructions for how to install](http://dev.deluge-torrent.org/wiki/Plugins#InstallingPlugins)

If you run Deluge in non-Classic mode (daemon and client setup), take a look at [Running a server/seedbox with a Deluge daemon](http://dev.deluge-torrent.org/wiki/Plugins#Client-ServerSetups)

### Configuring [IfaceWatch](/ifacewatch)

When enabling the plugin in Deluge a new tab is created in the Deluge prefences for [IfaceWatch](/ifacewatch).
The settings allows specifying a network interface, such as **eth0**, to be
monitored for changes at the interval specified in the setting.

In a VPN scenario where you want only the torrent traffic to pass through the VPN interface
it is necessary to manually set up routing table rules for this traffic. When the IP changes for
an interface, [IfaceWatch](/ifacewatch) will only instruct Deluge to change the IP that libtorrent listens on.
Therefore it is necessary to adjust the routing table rules as well when the IP changes.

