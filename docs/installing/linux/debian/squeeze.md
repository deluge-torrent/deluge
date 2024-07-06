# Debian Squeeze

If you require the latest version of Deluge than what is currently in the Squeeze repository, there are two options open to you:

## Unstable Repository

This method installs the latest Deluge version by using the Debian unstable distribution repository.

First add unstable to your `/etc/apt/sources.list`:

```
deb http://ftp.us.debian.org/debian unstable main
deb-src http://ftp.us.debian.org/debian unstable main
```
*Note: You should use your local country mirror, eg `ftp.uk.debian.org`, `ftp.fr.debian.org` etc.*

Next set the priority for each distribution so that only packages you specify are from unstable, not your whole system.

Edit `/etc/apt/preferences`

```
Package: *
Pin: release o=Debian,a=squeeze
Pin-Priority: 900

Package: *
Pin: release o=Debian,a=unstable
Pin-Priority: 300

Package: *
Pin: release o=Debian
Pin-Priority: -1
```

Update your packages list:

```
aptitude update
```

Now install the version of Deluge available in unstable:

```
aptitude -t unstable install deluge
```


## Deluge Launchpad PPA
The alternative to using Debian unstable involves using the Deluge Launchpad PPA for Ubuntu Maverick as the release is old enough to not get any unmet dependencies when installed on Squeeze.

*This method does not work for Lenny as it depends on a package that doesn't exist, see [Installing Lenny](/installing/linux/debian/lenny)*

Add PPA to your `/etc/apt/sources.list`:

```
deb http://ppa.launchpad.net/deluge-team/ppa/ubuntu maverick main
deb-src http://ppa.launchpad.net/deluge-team/ppa/ubuntu maverick main
```

Add repository GPG key to verify the downloaded packages:

```
apt-key adv --recv-keys --keyserver pgp.surfnet.nl 249AD24C
```

Refresh apt:

```
apt-get update
```

Install Deluge:

```
apt-get install -t maverick deluge-common deluged deluge-web
```

To also upgrade libtorrent to 0.15:

```
apt-get install -t maverick libtorrent-rasterbar6 python-libtorrent
```