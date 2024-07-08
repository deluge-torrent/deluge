
# Deluge FAQ

---
## General

### Is Deluge Free? Can I get the source?

Yes, Deluge is Free Software, as defined by the Free Software Foundation, and is released under the GPL, giving our users complete freedom. The source code is available in the [download section](/download.md). Our GPL nature allows you to be 100% sure that our program will never “spy” on your activities. Closed-source BitTorrent clients cannot make that same claim.

### How do I install Deluge?

[Installing](/installing/index.md)

### I have an issue starting or using Deluge.

See [Troubleshooting](/troubleshooting.md) and [Bug Reporting](/contributing/bugreporting.md)

### How to start the various user-interfaces?
See [UI specific questions](/faq.md#user-interface-specific)

### How do I set Deluge as my default BitTorrent program?

On Windows, the installer should do this automatically. On Linux/Unix (GNOME), right-click on a torrent file, click on properties, click on the "open with" tab. Is Deluge listed there? If so, select it to be your default, if not, click on "add", then click on "use custom command". Insert `/usr/bin/deluge` and click add.

### How do I set Deluge as my default program for Magnet URIs?

#### Gnome

Users can associate Magnets with Deluge with the following commands:

```
gconftool-2 -t string -s /desktop/gnome/url-handlers/magnet/command 'deluge "%s"'
gconftool-2 -t bool -s /desktop/gnome/url-handlers/magnet/needs_terminal false
gconftool-2 -t bool -s /desktop/gnome/url-handlers/magnet/enabled true
```

Also may require running the following:

```
gvfs-mime --set x-scheme-handler/magnet deluge.desktop
```

#### Firefox

Users can reset the Magnet association with:

  * Put `about:config` into address bar and change `network.protocol-handler.expose.magnet` to `false`.
  You will be prompted next time you click a Magnet to set an association with Deluge. (e.g. `/usr/bin/deluge`)
* **Windows** users should simply re-run the installer and select the magnet association option.
* **OSX** GTK does not support Magnet URIs (see [#2420](https://dev.deluge-torrent.org/ticket/2420)) but there is a plugin available: http://forum.deluge-torrent.org/viewtopic.php?f=9&t=52619

### Where does Deluge store its settings/config?

The default location for the Deluge config directory is in the `home` directory of the current user. The config location can be manually changed by using the `--config` option at startup.

 Linux, BSD and Mac OSX::
    `~/.config/deluge`

 Windows OS::
    `%APPDATA%\deluge`

*When running Deluge as a service the config directory is relative to the user specified in the service configuration.*

### Where does Deluge store the .torrent files?

Within the Deluge config in a directory named `state`.

### How do I reset the settings back to default?

If you don't care about losing your current torrents then delete everything in Deluge's [config](/faq.md#where-does-deluge-store-its-settingsconfig) directory.

If you do want to keep your current torrents then delete everything except for the `state` folder.

## User Interface Specific
### GTK UI
#### How do I start the GTK UI?
The main graphical interface. Can be started with either of the following:

```
deluge
```

```
deluge-gtk
```

### Web UI
#### How do I start the Web UI?
The web interface enables access to Deluge from your browser.

There are two ways to enable this interface:

1. From the GTK UI you can enable the `WebUI` plugin.
2. If running the Deluge daemon `deluged` it is recommended not use the plugin and instead run the standalone Web UI:

```
deluge-web
```

Open the browser at `http://localhost:8112`.

#### What is the default password

The Web UI default password  is `deluge`.

For security you should change this upon first login.

#### How do I change the password?
In the Web UI:
1. Click on `Preferences`.
2. Select the `Interface` category.
3. Fill out the fields under `Password`.
4. Click `Change` button.

#### How can I reset forgotten password?

1. Stop the Web UI before modifying the `web.conf` file.
2. Edit `web.conf` in [config](/faq.md#where-does-deluge-store-its-settingsconfig) and delete the entire `pwd_sha1` line or use quick method via command-line e.g.:

```
sed -i.bak "/pwd_sha1/d" ~/.config/deluge/web.conf
```
3. Start the Web UI and the password will have been reset to default password `deluge`.

#### How do I configure plugins with the Web UI?
Not all plugins are configurable directly with the Web UI, see [Plugins] table for those with Web UI code.

The easiest way to configure plugins is using the GTK UI. If unable to use GTK UI on the machine with your daemon, it is possible to connect to that daemon from another computer with the GTK UI. See [ThinClient](/userguide/thinclient.md) for more information on remote GTK UI setup.

#### How do I auto-connect to a specific daemon?

1. Stop the Web UI before modifying the `web.conf` file.
2. Edit `web.conf` in [config](/faq.md#where-does-deluge-store-its-settingsconfig), find `"default_daemon"` and set its value to the daemon `id` in `hostlist.conf`

   e.g. To connect to localhost you would open `hostlist.conf` as see a snippet such as:

```
...
      "123459d5a5b414159caa1323f6e0c9b240c7abcd",
      "localhost",
      58846,
...
```
1. Use the first entry from hostlist, which is the `id` and add it to `web.conf`:

```
"default_daemon": "123459d5a5b414159caa1323f6e0c9b240c7abcd",
```
1. Restart the Web UI.

#### How do I enable HTTPS?

1. Create a (self-signed) SSL certificate: http://httpd.apache.org/docs/2.0/ssl/ssl_faq.html#selfcert
2. Put the resulting `deluge.crt` and `deluge.key` in the [config's](/faq.md#where-does-deluge-store-its-settingsconfig) `ssl` directory.
3. Enable HTTPS in Web UI config and modify the filepaths to match the above files.
4. Restart the Web UI.

#### Can I bind the Web UI to port 80 in Linux?
You cannot bind to anything under 1024 in Linux, however with kernel >=2.6.24, you can use capabilities to allow Python to bind to port 80 securely.

So for example in Debian or Ubuntu:

1. `sudo apt-get install libcap2-bin`
2. `sudo setcap 'cap_net_bind_service=+ep' /path/to/python`
3. Configure the Web UI to use port `80`
4. Restart the Web UI.

### Console UI

#### How do I start the Console UI?
*Note: Requires the Deluge daemon `deluged` to be running.*

The text-based interface, ideal for terminal use:

```
deluge-console
```

The console can be also run in a non-interactive mode which outputs to the terminal:

```
deluge-console "info [torrent]"
```

#### How can I run multiple commands from the terminal?

Use `;` to separate commands and enclose the commands with double quotes `"`:

```
deluge-console "connect host user pass; info"
```


#### How do I connect the console UI to a daemon on a non-default port?

```
$ deluge-console
>>> connect localhost 12345
```

#### I encountered `BadLoginError("Password does not match")` with localhost daemon?

This is likely due to mismatching config locations, ensure you are running deluge-console with same user as deluged: [More Details](/userguide/thinclient.md#accessing-deluged-service-with-local-ui-client)

### Daemon

#### Why is Deluge still listed in my task manager even after I close it?

You closed only the UI, but you did not close the daemon.
Choose "Quit & Shutdown Daemon" to close both Daemon and GTK UI.

#### How do I start and stop the daemon?

```
deluged
```

```
pkill deluged
```

*Note: Deluge accepts the `SIGTERM` signal and cleanly shuts down.*

#### How do I start the daemon with logging enabled?

See: [Troubleshooting - Enable Logging](/troubleshooting.md#enable-deluge-logging)

Using the `--do-not-daemonize` (`-d`) option you can also log to console:

```
deluged -d [-L <loglevel>] [-l <logfile>]
```

#### I can't connect to the daemon from another machine

See [ThinClient](/userguide/thinclient.md) for more information but the summary steps are:

1. Configure the daemon to allow remote connections
2. Configure [Authentication](/userguide/authentication.md)
3. Restart the daemon.

#### How do I make Deluge connect to a different daemon?

By default, Deluge (GTK UI) is in classic mode, the daemon and GTK UI are linked together.

To disable classic mode:

1. `Preferences` -> `Interface`
2. Disable (untick) `Classic Mode`
3. Restart Deluge and it will now start in thin-client mode
4. Use the Connection Manager to enter the other daemon details
5.
See [ThinClient](/userguide/thinclient.md) for more information on remote GTK UI

#### How do I stop Deluge from killing the daemon when I quit the GTK UI?

See above.

## BitTorrent Related

### The files tab shows a different percentage-completed than the torrent

The files tab will only show percentages based on completed pieces while the main view will show total completed including incomplete pieces.

### What do all those numbers in parentheses mean?

| **Field** | **#** | **(#)** |
|-----------|-------|---------|
| Seeders | Number of connected seeders | Total number of seeders |
| Peers | Number of connected peers | Total number of peers |
| Downloaded | Total amount downloaded | Total amount downloaded this session |
| Uploaded | Total amount uploaded | Total amount uploaded this session |

### Seeding torrents have no queue position! Why?

Seeds use something called "seed rank" to determine which should be active and which should be queued.  The seed rank is determined by the number of seed cycles a torrent has completed.  Torrents with fewer completed seed cycles are prioritized for seeding.  A seed cycle is completed when a torrent meets either the share ratio limit (uploaded bytes / downloaded bytes), the share time ratio (time seeding / time downloading) or seed time limit (time seeded).

### What bandwidth settings should I use?

Start with the following:

|                   |   |
|-------------------|---|
|Maximum Connections|200|
|Maximum Download Speed (Kib/s)|-1|
|Maximum Upload Speed (Kib/s)|80% of upload speed|
|Maximum Upload Slots|4|
|Maximum Half-Open Connections|20|
|Maximum Connection Attempts per Second|20|

If you're using Windows XP*:

|                             | |
|-----------------------------|-|
|Maximum Half-Open Connections|8|

If you're using pre-SP2 Windows Vista*:

|                             | |
|-----------------------------|-|
|Maximum Half-Open Connections|4|

You can then tweak those settings to suit your connection.  See [Bandwidth Tweaking](/userguide/bandwidthtweaking.md).

Note: if you do not know your upload speed, go to http://speedtest.net and run a test. You can view the results in KB/s by choosing "kilobytes" for "Speed Measurement" which can be accessed under "Settings" in the top left corner of the page.

* If you have Deluge setup as a [ThinClient](/userguide/thinclient.md) then this setting is determined by the OS the daemon is running on, not the thin client.


### Deluge sometimes creates files that I didn't ask it to download?

Deluge handles files as pieces, not as individual files. This gets tricky, as sometimes the same piece is shared between consecutive files. So if you tell Deluge to download a file, it'll download all of the pieces within that file, and if one of those pieces is shared with another file, that file will also be created, although not necessarily entirely downloaded.

Note: Deluge can be run with experimental libtorrent from libtorrent_aio branch. In this case all pieces of not wanted files will be stored in one temporary file per torrent.

### I lost data on force recheck?

Force recheck discards all incomplete pieces.

### Does Deluge support Initial or Super Seed?

Not yet, but it will be added in a future release, see [#1903](https://dev.deluge-torrent.org/ticket/1903).

### Does Deluge have an embedded tracker?

No and it probably never will. We want to be the best BitTorrent client around, and to do that we need to focus on just being a client.

### Does Deluge support multi-tracker torrents?

Yes it does. You can edit the trackers associated with a torrent by right-clicking on a torrent within Deluge, and clicking on “Edit Trackers.”

This conforms to the BitTorrent Multitracker [specifications](http://wiki.depthstrike.com/index.php/P2P:Protocol:Specifications:Multitracker)

### What is the difference between full allocation and compact allocation?

Compact allocation only allocates as much storage as it needs to keep the pieces downloaded so far. This means that pieces will be moved around to be placed at their final position in the files while downloading (to make sure the completed download has all its pieces in the correct place). In full allocation, the entire space that a file needs is allocated as soon as one piece of that file is downloaded, thus decreasing fragmentation.

We suggest that our users use full allocation.

Deluge uses [sparse files](http://en.wikipedia.org/wiki/Sparse_file) for full allocation, the compact allocation option is only useful on file systems that don't support sparse files (such as FAT or HFS+).

### Selective downloading isn't working. How come?

Selective downloading requires full allocation, check you are not using compact allocation. See above for details between the two.

### Which ports should I use?

The official ports for Bittorrent are `6881-6889`, but most ISPs block or at least throttle those ports, so users are encouraged to use a port range of something between `49152` and `65535`.

### Deluge uses random ports instead of selected one, why?

You will need to click OK or Apply in Preferences after changing the port however Deluge will pick a random port if the chosen port is not available.

Run `netstat` to check if the port is free.

### What does "Auto Managed" do?

An "auto managed" torrent, is a torrent managed by Deluge.
This means that it obeys Deluge's queue settings.
By disabling "auto managed", a torrent will become active (i.e. start downloading/uploading).
It will still be be bound by the stop ratio though (see 'Stop seed at ratio' under the Queue section of the torrent's Options tab).

Note: All active torrents (including those not "auto managed") are counted in the total active queue settings. This means that if the total number of active torrents ("auto managed" and not) exceed the limit for total active torrents in the queue settings, Deluge will automatically queue any "auto managed" torrents until the limit is no longer exceeded.

### Does Deluge have an equivalent to "Force Start"?

Deluge has "auto managed" torrents which are similar, see above for details.

To make a torrent no longer "auto managed":
1. Select the torrent in question.
2. Select the options tab.
3. Unselect "Auto Managed".

### What is a Magnet URI?
Magnet URIs are an easy way to add torrents by their info-hash.  You can learn more about them [here](http://en.wikipedia.org/wiki/Magnet_URI_scheme).

### What is Peer TOS Byte?
IPv4 Header Type Of Service Byte [http://shorewall.net/manpages/shorewall-tcclasses.html (More Info)](http://shorewall.net/manpages/shorewall-tcclasses.html (More Info))

Masks: Normal Service `0x00`, Minimize Cost `0x02`, Maximize Reliability `0x04`, Maximize Throughput `0x08`, Minimize-delay `0x10`

### Can Deluge use blocklists such as SafePeer or PeerGuardian?

You can use the [Blocklist Plugin](/plugins/blocklist.md).

### I have a status bar warning: "No Incoming Connections!"

You need to configure your router or firewall to allow (unblock) incoming torrent traffic for the network ports that Deluge uses.

Enabling `UPnP` in Deluge and on your router can automatically open the ports as needed.

## Enable Deluge Logging

[troubleshooting.md#enable-deluge-logging](/troubleshooting.md#enable-deluge-logging)