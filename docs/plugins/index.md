# Plugins

---

## Plugins (Included)

| **Name**                        | **Description**                                                     | **WebUI**            |
| ------------------------------- | ------------------------------------------------------------------- | -------------------- |
| [AutoAdd](/plugins/autoadd.md)     | Multiple watch folder support                                       | _Yes_                |
| [Blocklist](/plugins/blocklist.md) | Download and import IP blocklists                                   | _Yes_                |
| [Execute](/plugins/execute.md)     | Executes a command upon an event                                    | _Yes_                |
| Extractor                       | Extracts files upon completion                                      | _Yes_                |
| Label                           | Assign labels to torrents for custom actions                        | _Yes_                |
| Notification                    | Provides Email, Popup, Blink and Sound notifications                | _Yes_                |
| Scheduler                       | Limit Deluge bandwidth depending on schedule                        | _Yes_                |
| [Stats](/plugins/stats.md)         | Displays pretty graphs of statistics                                | _No_                 |
| WebUI                           | Start the web interface from within Deluge                          | _Infinite recursion_ |
| [Toggle](/plugins/toggle.md)       | Allows the users to set the session to either "paused" or "resumed" | _No_                 |

---

## Plugins (3rd Party)

| **Name**                                                                        | **Description**                                                                       | **WebUI** | **Deluge 2.x support** |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | --------- | ---------------------- |
| [AutoPriority](/plugins/autopriority.md)                                           | Downloads torrents in alphabetical order                                              | _No_      | _No_                   |
| [AutoShutdown](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=41165)       | Shutdown or hibernate computer when all torrents complete downloading                 | _No_      | _No_                   |
| [Auto Remove](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=36443)        | Limit the number of inactive torrents that are kept                                   | _No_      | _No_                   |
| [Auto Remove Plus](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=47243)   | Based on Auto Remove but with more features                                           | **Yes**   | **Yes**                |
| [Batch Renamer RegEx](https://github.com/Grewfisk/BatchRenamerRegEx/releases)   | Batch rename files in a torrent using regex search and replace. Fork of Batch Renamer | _No_      | _No_                   |
| [Browse Button](https://github.com/dredkin/deluge-rbb/releases)                 | Browse destination folders in client-server mode                                      | _No_      | **Yes**                |
| [CopyMagnetURI](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=47501)      | Copy the magnet URI of the selected torrent(s) to the clipboard                       | _No_      | _No_                   |
| [Default Trackers](https://github.com/stefantalpalaru/deluge-default-trackers)  | Add default trackers for all your new torrents                                        | _No_      | **Yes**                |
| [FileBotTool](https://github.com/Laharah/deluge-FileBotTool)                    | Integrates automatic media sorting using [FileBot](http://www.filebot.net/)           | _No_      | **Yes**                |
| [IfaceWatch](/plugins/ifacewatch.md)                                               | Watch for IP changes on specific interfaces and notify libtorrent                     | _No_      | **Yes**                |
| [IPstatusbar](https://github.com/cas--/deluge-ipstatusbar/releases)             | Show the external IP address being listened on in the status bar                      | _No_      | _No_                   |
| [LabelPlus](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=42629)          | Labeling plugin with additional features                                              | _No_      | **Yes**                |
| [ltConfig](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=42887)           | Configure libtorrent settings                                                         | **Yes**   | **Yes**                |
| [MyScheduler](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=54025)        | Scheduler with Force Start                                                            | **Yes**   | _No_                   |
| [NetWatcher](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=40769)         | Monitors the local network activity and deciding if pause or resume all torrents.     | _No_      | _No_                   |
| [NetWatcher2](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=47327)        | Monitors the local network activity and automatically limits the download speed.      | _No_      | _No_                   |
| [Pieces](/plugins/pieces.md)                                                       | View status and set priority of each individual piece of a torrent                    | **Yes**   | _No_                   |
| [PreventSuspend](/plugins/preventsuspend.md)                                       | Prevents computer suspending                                                          | _No_      | _No_                   |
| [PreventSuspendPlus](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=52115) | Prevents computer suspending (inc Windows support)                                    | **Yes**   | _No_                   |
| [Ratio](https://forum.deluge-torrent.org/viewtopic.php?f=9&t=54864)             | Show total downloads, uploads, and overall share ratio in status bar.                 | _No_      | _No_                   |
| [Randomize](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=38747)          | Randomizes incoming port based on configurable interval and blocked port check        | _No_      | _No_                   |
| [SeedTime](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=39767)           | Pause or remove torrents after they have seeded for a certain amount of time.         | _No_      | _No_                   |
| [SequentialDownload](https://github.com/hrushikesh198/DelugeSequentialDownload) | Download pieces in sequential order for watching while downloading.                   | _No_      | _No_                   |
| [Smart Move](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=40835)         | Displays move storage progress in status bar.                                         | _No_      | _No_                   |
| [Streaming](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=49679)          | Stream video or audio directly from Deluge while downloading                          | **Yes**   | **Yes**                |
| [Telegramer](https://github.com/noam09/deluge-telegramer)                       | Receive notifications, add and view torrents using Telegram messenger                 | **Yes**   | **Yes**                |
| [textTab](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=53953)            | Displays the contents of a text file in a new tab                                     | _No_      | _No_                   |
| [Total Traffic](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=34025)      | Shows per session & optionally total traffic                                          | _No_      | _No_                   |
| [Traffic Limits](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=34343)     | Pause all torrents if more than a set amount of data is uploaded or downloaded.       | _No_      | _No_                   |
| [Updatorr](http://pypi.python.org/pypi/Updatorr/)                               | Automatic torrents updates for forum-like trackers                                    | _No_      | _No_                   |
| [uTorrentImport](https://github.com/Laharah/deluge-uTorrentImport)              | a cross platform Deluge plugin to import torrents from uTorrent                       | _No_      | _No_                   |
| [WebAPI](https://pypi.python.org/pypi/deluge-webapi)                            | Alternative JSON API for WebUI                                                        | **Yes**   | **Yes**                |
| [YaRSS2](/plugins/yarss2.md)                                                       | An RSS plugin configurable through the GUI                                            | _No_      | **Yes**                |

### Unmaintained Plugins
| **Name**                                                                     | **Description**                                                                                                          | **WebUI** | **Deluge 2.x support** |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------- | ---------------------- |
| [XMPP Notify](/plugins/xmppnotify.md)                                           | XMPP notify/control bot                                                                                                  | _No_      | _No_                   |
| [YaRSS](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=31553)           | Simple RSS plugin for TV Shows                                                                                           | _No_      | _No_                   |
| [Batch Renamer](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=35615)   | Rename multiple files in torrents for tidiness                                                                           | _No_      | _No_                   |
| [Categorise](/plugins/categorise.md)                                            | Moves downloaded torrent to a specific directory depending on type                                                       | _No_      | _No_                   |
| [Copy Completed](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=33995)  | Copies completed torrents to another location                                                                            | **Yes**   | _Unknown_              |
| [CopyLimit](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=39173)       | Controls upload "ratio" while downloading based on torrent total size                                                    | _No_      | _Unknown_              |
| [Delete Partials](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=28915) | Deletes partial files left by 'Do not download'                                                                          | _No_      | _No_                   |
| [Growl](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=32315)           | Growl Notifications for completed torrents                                                                               | _No_      | _Unknown_              |
| [LobberCore](http://git.nordu.net/?p=lobber-deluge-core.git;a=tree;f=dist)   | Automatic downloader and core functionality plugin for use with [Lobber](https://portal.nordu.net/display/LOBBER/Lobber) | _No_      | _Unknown_              |
| [Managed Pause](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=34001)   | Scheduler that allow you to exclude torrents                                                                             | _No_      | _Unknown_              |
| [MoveTools](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=42623)       | Monitor torrent move status                                                                                              | _No_      | _No_                   |

### Browser Plugins

| **Chrome**   |   |
| --- | --- |
|[DelugeSiphon](https://chrome.google.com/webstore/detail/gabdloknkpdefdpkkibplcfnkngbidim)| Ultra simple Chrome extension to add torrents via WebUI interface. |
|[Deluge Remote](https://chrome.google.com/webstore/detail/remote-deluge/epcolmlaegimilnokaddncgmdafacohf)| Provides a simple overview of current torrents within Chrome [(Source Code)](https://github.com/YodaDaCoda/chrome-deluge-remote)|


|  **Firefox**  |   |
| --- | --- |
|[DelugeAddTorrent](https://addons.mozilla.org/en-US/firefox/addon/delugeaddtorrent/) | Send the torrent magnet link to Deluge Web UI [(Source Code)](https://github.com/muriloportugal/DelugeAddTorrent) |
|[BitTorrent WebUI+](https://addons.mozilla.org/en-US/firefox/addon/bittorrent-webui-120685/)| Automatically add torrent/magnet links via WebUI |
|[WebUI Quick Add Torrent ](http://userscripts-mirror.org/scripts/show/79003.html) | Uses Greasemonkey to add a clickable icon on webpages for adding torrents via WebUI |


### Application Plugins

_Extensions or scripts for applications that enable interaction with Deluge_

| **Name**                                                                                        | **Description**                                                                                                                                       |
| ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| [OSX Magnet URI Handler](https://github.com/Lord-Kamina/Deluge-Magnet-Handler)                  | OSX Applescript handler to open magnet URLs in Deluge.app                                                                                             |
| [RCDefaultApp](http://www.rubicode.com/Software/RCDefaultApp/)                                  | General preference pane to configure default apps, used to link magnet links to Deluge-Magnet-Handler on newer macs                                   |
| [ConkyDeluge](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=30825)                        | Script to display Deluge statistics within Conky                                                                                                      |
| [Docky Helper](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=30985)                       | Docky helper that shows transfer rates on the Deluge badge                                                                                            |
| [FlexGet Plugin](http://flexget.com/wiki/Plugins/deluge)                                        | Deluge Plugin for the advanced RSS tool [(More Info)](/plugins/flexget.md)                                                                               |
| [FileBot Script](http://forum.deluge-torrent.org/viewtopic.php?f=9&p=172841#p172841)            | Uses [Execute](/plugins/execute.md) plugin to run [filebot](http://filebot.sourceforge.net/) which renames, categorizes, and finds subtitles and artwork |
| [Inoreader](https://github.com/maziara/deluge-feed-inoreader)                                   | Tag the articles in Inoreader and they will be downloaded in Deluge                                                                                   |
| [Periscope Subtitle Script](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=38957&p=163277) | Uses [Execute](/plugins/execute.md) plugin to run a subtitle searching script based around [periscope](https://code.google.com/p/periscope/) module      |
| [Transdroid](http://www.transdroid.org/download/using-deluge-on-ubuntu/)                        | Manage your torrents from your Android device                                                                                                         |
| [XBMC Plugin](http://code.google.com/p/deluge-xbmc-plugin/)                                     | Connects via WebUI to display and manipulate the status of torrents within XBMC                                                                       |
| [Plex Script](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=46529)                        | Uses [Execute](/plugins/execute.md) plugin for managing an automated [plex media server](https://plex.tv/) setup.                                        |

---

## Installing Plugin Eggs

### Determine Python Version

Plugin eggs have the _Python_ version encoded in the filename and will only load in Deluge if the Python versions match.

- Verify Deluge [Python version](/troubleshooting.md#python-version).

### Download

Download the plugin `egg` that matches the Deluge Python version from above, e.g.

- _Plugin-1.0-**py2.6**.egg_ is a _Python 2.6_ egg.
- _Plugin-1.0-**py2.7**.egg_ is a _Python 2.7_ egg.

For plugins that don't have a specific Deluge Python version available::
It is possible to rename an egg to match the Python version (e.g. _Plugin-1.0-**py2.6**.egg_ _to_ _Plugin-1.0-**py2.7**.egg_) and should still work.

### Install

GUI::
`Preferences -> Plugins` click `Install plugin`, locate the downloaded plugin `egg` and select it to install.

Manually::
Copy the plugin `egg` to the Deluge [config](/faq.md#where-does-deluge-store-its-settingsconfig) `plugins` directory:

If the Plugin does not show up in the Plugins list then it is likely the incorrect Python version of the plugin has been installed, also see below.

#### Client-Server Setups

When running the Deluge daemon, `deluged` and Deluge client on a separate computers, the plugin must be installed on both machines. Installing a plugin egg through the GTK client will copy the egg to both the local plugins directory, as well as the remote daemon's. However if the Python versions on the local machine and remote server do not match, you will have to copy the egg to the remote server manually.

For example in the setup below you will have to install the py2.6 egg on the local machine but then _manually_ install the py2.7 egg onto the remote server.

- Local machine with Python 2.6 running `GTKUI` client.
- Remote server with Python 2.7 running `deluged`.

See [Determine Python Version](/plugins/index.md#determine-python-version) above.

## Plugin Development

- [Plugin Development](/development/plugins/index.md)
- [PluginIdeas](/development/plugins/pluginideas.md)
