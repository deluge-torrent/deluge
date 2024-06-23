# Installing Deluge on Mac OSX

## Deluge.app

A Deluge.app package is available for [download](http://download.deluge-torrent.org/mac_osx/)

---

## MacPorts

These instructions and [portfile](https://www.macports.org/ports.php?by=name&substr=deluge) work on OSX Snow Leopard 10.6 & Lion 10.7 with Deluge 1.3.x. They also assume a clean install of OSX (no XQuartz, Darwine, Winebottler, or MacPorts / Fink installed).

This methodology is time consuming, but less error-prone for the uninitiated. It will take a few hours normally to download and compile along with using several gigabytes of disk-space.


### Prerequisites

Download and install:

* Xcode from App Store
* [MacPorts](http://www.macports.org) *(v2.0.3 as of writing)*

### Installation

There are two interface options when installing Deluge, one is to use **X11**, the other **Quartz-GTK**. `X11` is the *classic* Linux interface, while `Quartz-GTK` uses the native OSX interface. The `Quartz-GTK` is faster and looks better but is a bit more error prone, so it is up to you.

Open Terminal (under Utilities) and all the following steps will be done from here.

#### X11 Interface

```sh
sudo port install deluge
```

#### Quartz-GTK Interface

```sh
sudo port install deluge +no_x11 +quartz 
```

### Start Deluge

1. Open Terminal, assuming port is in your path (/opt/local/bin)
2. Start deluged daemon:

```sh
deluged-2.7 &
```
1. Start deluge interface:

```sh
deluge-2.7 &
```

### Optional Steps

#### GTK Engines
To get a better looking interface, you can install gtk-engines2 (or others [GTK engines](http://www.macports.org/ports.php?by=name&substr=engine)) :

```sh
sudo port install gtk-engines2
```

Then set you preferred engine (clearlooks in this case, which is nice)

```sh
echo 'gtk-theme-name = "Clearlooks"' | sudo tee /opt/local/etc/gtk-2.0/gtkrc
```

#### Language
If you prefer english version (or any other language) you can launch deluge using the following:

```sh
export LANG=en_US && deluge-gtk-2.7 &
```

Or alternatively, you can use an alias (in your bash profile, zshrc...)

```sh
alias deluge='export LANG=en_US && deluge-gtk-2.7 &'
```

### More
More details / help available on forums! in [OSX Section](http://forum.deluge-torrent.org/viewforum.php?f=13) and also in [this thread](http://forum.deluge-torrent.org/viewtopic.php?f=13&t=34649) which initiated that wiki page.