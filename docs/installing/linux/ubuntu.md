# Ubuntu Install Guide

## Install Deluge

**Software Centre**:
 [Deluge](http://apt.ubuntu.com/p/deluge)


**GUI install from Terminal:**

```sh
 sudo apt-get install deluge
```

**Headless install from Terminal:**

```sh
 sudo apt-get install deluged deluge-web deluge-console
```

Although Deluge is included in the official [Ubuntu repositories](http://packages.ubuntu.com/search?keywords=deluge-torrent) it may be out of date. To ensure you are using the latest version use the [PPA Repository](/installing/linux/ubuntu.md#deluge-ppa-repository), see the steps below.

### Deluge PPA Repository
The [Deluge PPA](https://launchpad.net/~deluge-team/+archive/stable) contains the latest Deluge releases for Ubuntu.

```sh
sudo add-apt-repository ppa:deluge-team/stable
sudo apt-get update
sudo apt-get install deluge
```

## Removing

```sh
  sudo apt-get remove deluge
```
