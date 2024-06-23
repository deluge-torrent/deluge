# Before Reporting a Bug

- Install the latest version of Deluge: **Version**

- Check the **[Frequently Asked Questions](/faq)**.

## Search for Existing Issues

_Frequently questions from users often relate to already fixed or known about bugs in Deluge so please search before asking._

- **[search: Deluge Bug Tickets]**

- **[Deluge Forum](http://forum.deluge-torrent.org/search.php)**

- Deluge site search using a [Search Engine](https://www.google.co.uk/search?q=site:deluge-torrent.org)

## Ask your Question Effectively

Two links that provide helpful generic tips for reporting software problems.

[How To Ask Questions The Smart Way](http://www.catb.org/~esr/faqs/smart-questions.html#before)

[How to Report Bugs Effectively](http://www.chiark.greenend.org.uk/~sgtatham/bugs.html)

# Collect Bug Information

You will need the following information when reporting a bug, Deluge and libtorrent versions are essential:

- Version Information:

  - [Deluge version](/troubleshooting#delugeversion).
  - [libtorrent version](/troubleshooting#libtorrentversion).
  - Operating System and version.
  - Browser and version _(if using WebUI)_.

- Plugins enabled.
- Language in use _(if not in English)_.
- Installation method _i.e. from source, package or installer_.

- Precise steps to reproduce the bug.

- [Deluge Logs](/troubleshooting#enabledelugelogging) (`error` level is usually fine in first instance).
- Information of any errors or traces.
- [Config](/faq#wheredoesdelugestoreitssettings) files.
- Screenshots and screencasts are helpful for GUI issues.

_Note: If you are using Client and Daemon you may need version or logs from both._

## Hard Crashes of Deluge (or libtorrent)

A backtrace using `gdb` may be required for hard crashes of Deluge (crashes without an obvious error in Deluge logs).

Here is a _deluged_ example:

```
   gdb --args python /usr/bin/deluged -d
   (gdb) run
   ## After Crash ##
   (gdb) thread apply all backtrace
```

# Opening a Bug Ticket

The bug ticket system we use is called Trac. [/register Sign up] if you haven't already.

_Note: The Trac user account is separate to the Forum user account._

1. [/newticket Create a new bug ticket]
2. Fill in the boxes, making sure the following are completed:
   - _Summary:_ Short description of issue
   - _Description:_ Include the steps to reproduce and other collected information, use `{{{ }}}` markup for pasting code or errors.
   - _Version:_ Deluge version
   - _Component:_ Best guess as to where the problem occurs
3. Attach any logs, screenshots or patches

# External bug trackers

These sites also track bugs relating to Deluge or libtorrent.

- [Ubuntu](https://bugs.launchpad.net/ubuntu/+source/deluge), [Fedora](https://apps.fedoraproject.org/packages/deluge/bugs), [Debian](http://bugs.debian.org/cgi-bin/pkgreport.cgi?src=deluge), [Arch](https://bugs.archlinux.org/index.php?string=deluge), [Gentoo](https://bugs.gentoo.org/buglist.cgi?quicksearch=deluge), [MacPorts](http://trac.macports.org/query?status=assigned&status=new&status=reopened&order=priority&port=deluge)

**libtorrent (rasterbar) Bugs:**

- [libtorrent issue tracker](https://github.com/arvidn/libtorrent/issues), also [Ubuntu](https://bugs.launchpad.net/ubuntu/+source/libtorrent-rasterbar), [Fedora](https://admin.fedoraproject.org/pkgdb/acls/bugs/rb_libtorrent), [MacPorts](http://trac.macports.org/query?status=assigned&status=new&status=reopened&order=priority&port=libtorrent-rasterbar)
