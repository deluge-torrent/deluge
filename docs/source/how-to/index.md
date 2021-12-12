# How-to guides

A collection of guides covering common issues that might be encountered using Deluge.

## GTK UI

```{toctree}
:titlesonly:

Set default torrent application <set-mime-type>
```

## Deluge as a service

Services are used to start applications on system boot and leave them running
in the background. They will also stop the application nicely on system
shutdown and automatically restart them if they crash.

The Deluge daemon deluged and Web UI deluge-web can both be run as services.

```{toctree}
:titlesonly:

Create systemd services for Linux <systemd-service>
Create launchd services for macOS <launchd-service>
Create NSSM services for Windows <nssm-service>
```
