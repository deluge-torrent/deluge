# Debian Jessie

Install using the default package version of Deluge (this means you won't get an up to date version, but it'll be updated automatically with your system)

## Install Deluge (GUI)

```
apt-get install deluge
```

## Install (headless/server)

```
apt-get install deluged deluge-web
```


## Deluge Launchpad PPA

Install using the Deluge Ubuntu Launchpad PPA which contains the latest releases of Deluge and libtorrent.

```
add-apt-repository 'deb http://ppa.launchpad.net/deluge-team/ppa/ubuntu trusty main'
```

**OR** (if command not recognized)paste the below lines in /etc/apt/sources.list

```
#Deluge PPA
deb http://ppa.launchpad.net/deluge-team/ppa/ubuntu trusty main
deb-src http://ppa.launchpad.net/deluge-team/ppa/ubuntu trusty main
```






Update and install

```
apt-get update
apt-get install -t trusty deluged deluge-web
```

To upgrade libtorrent:

```
apt-get install -t trusty libtorrent-rasterbar8 python-libtorrent
```

For config and systemd service setup see [systemd](/userguide/initscript/systemd) and [thinclient](userguide/thinclient) guides.

For `'add-apt-repository: command not found:` install `software-properties-common`.


