# How to create launchd services for macOS

The following launchd script uses a separate user deluge, this is optional
but recommended for security. To create a new deluge user follow the
​[Apple help] steps.

The paths to `deluged` and `deluge-web` assumes installation using [Homebrew]
and will need modified if using other installation methods e.g. `Deluge.app`.

## Daemon (deluged) service

Create the file `/Library/LaunchDaemons/org.deluge-torrent.deluged.plist`
containing the following:

```eval_rst
.. literalinclude:: ../../../packaging/osx/launchd/org.deluge-torrent.deluged.plist
    :language: xml
```

Set the service to load on startup and then start it:

```console
sudo launchctl load -w /Library/LaunchDaemons/org.deluge-torrent.deluged.plist
sudo launchctl start org.deluge-torrent.deluged
```

## Web UI (deluge-web) service

Create the file `/Library/LaunchDaemons/org.deluge-torrent.deluge-web.plist`
containing the following:

```eval_rst
.. literalinclude:: ../../../packaging/osx/launchd/org.deluge-torrent.deluge-web.plist
    :language: xml
```

Set the service to load on startup and then start it:

```console
sudo launchctl load -w /Library/LaunchDaemons/org.deluge-torrent.deluge-web.plist
sudo launchctl start org.deluge-torrent.deluge-web
```

## Logging

Logging is enabled by default in the above script, error level, and can be
modified as required.

[apple help]: https://support.apple.com/en-gb/guide/mac-help/mtusr001/mac
[homebrew]: https://brew.sh/
