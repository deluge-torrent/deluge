
<h1 style="text-align: left;">Deluge TroubleShooting</h1>


# General

## Deluge won't start! What should I do?

Common startup errors with solutions:

* `ImportError: No module named libtorrent`
    * You need to install [libtorrent-rasterbar](http://www.rasterbar.com/products/libtorrent/).

* `gobject.GError: Unrecognised image file format`
    * You need to install SVG support. On !Debian/Ubuntu, the package is `librsvg2-common`.

* Windows OS: `Deluge not starting` or `Error:14001 side-by-side configuration`
    * Install *vcredist_x86.exe*: [Visual C++ 2008 SP1 Redistributable Package](https://www.microsoft.com/en-us/download/details.aspx?id=26368)

**For any other issues not solved here see** [Bug Reporting](/contributing/bugreporting.md) **and follow the detailed steps.**

## Deluge's GTK UI won't connect to a remote daemon

Make sure both the GTK UI and the daemon are the same (or similar, e.g. 1.3.x) versions.

Otherwise make sure you've followed the [thin client userguide](/userguide/thinclient.md).

## Deluge isn't working! What should I do?

See [Bug Reporting](/contributing/bugreporting.md)

If you are pasting the log on the forums, please use the `[code][/code]` tags.

If you are pasting the log on IRC, please use [dpaste](http://dpaste.com) or [pastebin](http://pastebin.com) or something similar.

## How do I add an already completed torrent to Deluge?

If you add an already completed torrent to Deluge, you just need to set `Download Location` to the path where your data is, and Deluge will continue downloading/seeding the torrent.

A common error occurs if your torrent contained a folder. If your torrent contained a folder called Torrent.Name.2010, such that the data was in ~/downloads/Torrent.Name.2010/ You need to set the download location to ~/downloads/ **not** ~/downloads/Torrent.Name.2010/

If you have already added the torrent to Deluge, you can pause it, select 'Move Storage', point it to your data, then choose 'Force Re-check'

## Torrent stuck at 99% or some other point, even though seeders available

Check that local machine firewall or router is not detecting a SYN flood and blocking packets. As a torrent reaches completion and you become a seeder, there can be a sudden inrush of connections from other peers that causes firewalls to start blocking. If so, try reducing the total connections allowed in Deluge, or increasing the tolerance on the router, or turning off SYN flood detection. Also check local storage for the downloaded file is not out of space (shown on bottom status bar in Deluge UI).

## Samba Network Shares

### Windows OS
To use a Samba share in Deluge from within Windows, the share has to be mapped to a drive letter.

## How can I change Deluge language?

### Windows OS
There is a bug in the way GTK sets language on Windows but there are several workarounds:

* [Set a global](http://www.howtogeek.com/51807/how-to-create-and-use-global-system-environment-variables/) `LANG` environment variable to the language you require, e.g. `en`.

* Create a cmd file to set the `LANG` and open deluge. Copy the following text into notepad:

    ```
    set lang=en
    start deluge.exe
    ```
  Save the file as `Deluge.cmd` in the same folder as `Deluge.exe`. Create a shortcut to the .cmd file and use it to start Deluge.

* To force the use of English only, delete the following language files from Deluge program folder:
    * `C:\Program Files\Deluge\deluge-1.3.x-py2.x.egg\deluge\i18n`
    * `C:\Program Files\Deluge\share\locale`

# Deluge Version

 GTKUI::
  Open `About` dialog from the application Help menu.

 From the terminal::
  `deluge --version`, `deluged --version`, etc.

## libtorrent version

The libtorrent version is in the output of [Deluge Version](/troubleshooting.md#deluge-version).

 From the terminal::
  `python -c "from deluge._libtorrent import lt; print lt.version"`

## Python Version

 Linux/*nix::
  Usually Python 2.7 is default but verify from terminal with: `python --version`

 Windows OS::
  Check the Deluge installed files: `%ProgramFiles%\Deluge\deluge-***-py2.6.egg` This would signify Deluge is running Python 2.6.

  The suffix to the installer can also indicate version so *deluge-1.3.x-win32-**py2.7**-setup.exe* would be Python 2.7.

 Mac OSX::
  For the Deluge.app the default is Python 2.7.

# Enable Deluge Logging
To enable logging run Deluge from a terminal with the following options.

* These options apply to all Deluge applications: `deluged`, `deluge-gtk`, `deluge-web` & `deluge-console`

## Logging to shell

```
deluge -L <loglevel>
```
## Logging to file

```
deluge -L <loglevel> -l <logfile>
```

## Available Log levels

* `none`
* `critical`
* `error`
* `warning`
* `info`
* `debug`

Note: `debug` is *very* verbose and with a lot of torrents log files will be MB's in size.

## Windows Specific Logging

You will need to use the `*-debug.exe` program versions to view errors that may be propagated to console and missed by logging.

e.g. Open a Command Prompt and run:

`"%ProgramFiles%\Deluge\deluge-debug.exe" -L error -l "%UserProfile%\Desktop\deluge.log"`





