# Deluge Service

## What is a service?

Operating systems use services to start applications on system boot and leave them running in the background. They will also stop the application nicely on system shutdown and automatically restart them if they crash.

The Deluge daemon `deluged` and Web UI `deluge-web` can both be run as services.

## Linux

Most Linux distributions now use systemd. See [wikipedia](https://en.wikipedia.org/wiki/Systemd#Adoption_and_reception) for releases with systemd as *default*.

* [systemd](/userguide-service/systemd)

* [Upstart](/userguide-service/upstart) *(ubuntu 11.04 to 14.10)*

* [init.d](/userguide-service/debianubuntuinitd) *(obsolete)*

## Microsoft Windows

* [Windows service](/userguide-service/ms_windows)

## Apple OS X

* [launchd](/userguide-service/launchd)

## FreeBSD

* [rc.d](/userguide-service/freebsd)