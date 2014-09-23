=========================
 Deluge BitTorrent Client
=========================

|build-status| |docs|

Homepage: http://deluge-torrent.org

Authors:
    Andrew Resch
    Damien Churchill

For contributors and past developers see: 
    AUTHORS

==========================
Installation Instructions:
==========================

For detailed instructions see: http://dev.deluge-torrent.org/wiki/Installing/Source

Ensure build dependencies are installed, see DEPENDS for a full listing.

Build and install by running::

    $ python setup.py build
    $ sudo python setup.py install

================
Contact/Support:
================

:Forum: http://forum.deluge-torrent.org
:IRC Channel: #deluge on irc.freenode.net

===
FAQ
===

For the full FAQ see: http://dev.deluge-torrent.org/wiki/Faq

How to start the various user-interfaces:
    Gtk::

        deluge or deluge-gtk

    Console::

        deluge-console

    Web::

        deluge-web
        Go to http://localhost:8112/ default-password = "deluge"

How do I start the daemon?:
    deluged

I can't connect to the daemon from another machine:
    See: http://dev.deluge-torrent.org/wiki/UserGuide/ThinClient


.. |build-status| image:: https://travis-ci.org/deluge-torrent/deluge.svg
    :target: https://travis-ci.org/deluge-torrent/deluge

.. |docs| image:: https://readthedocs.org/projects/deluge/badge/?version=develop
    :target: https://readthedocs.org/projects/deluge/?badge=develop
    :alt: Documentation Status