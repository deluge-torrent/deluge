# How-to guides

A collection of guides covering common issues that might be encountered using Deluge.

## GTK UI

- [Set default torrent application](set-mime-type.md)

## Deluge as a service

Services are used to start applications on system boot and leave them running
in the background. They will also stop the application nicely on system
shutdown and automatically restart them if they crash.

The Deluge daemon deluged and Web UI deluge-web can both be run as services.

- [Create systemd services for Linux](systemd-service.md)
- [Create launchd services for macOS](launchd-service.md)
- [Create NSSM services for Windows](nssm-service.md)
