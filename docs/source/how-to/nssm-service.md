# How to create NSSM services for Windows

Download ​[NSSM] and read their usage page about installing.

In order for the services to be stopped properly, use the debug application
versions (ending in `-debug.exe`).

## Daemon (deluged) service

Create a `deluged` service:

```console
nssm install deluged
```

The following are minimum UI changes required for the service to work:

```
Path: C:\Program Files\Deluge\deluged-debug.exe
Arguments: -c C:\config_location
```

## Web UI (deluge-web) service

```console
nssm install deluge-web
```

```
Path: C:\Program Files\Deluge\deluge-web-debug.exe
Arguments: -c C:\config_location
```

If Web UI is not accessible outside your machine (if you're running
Deluge from a home server), you have to whitelist Deluge in your Windows
Firewall for the `deluge-web` and `deluge-web-debug` executable.

[nssm]: http://nssm.cc/
