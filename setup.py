#
# setup.py
#

from distutils.core import setup, Extension

setup(name="Deluge", fullname="Deluge Bittorrent Client", version="0.5.0",
	author="Zach Tibbitts",
	description="A bittorrent client written in PyGTK",
	url="http://deluge-torrent.org",
	license="GPLv2",
	
	scripts=["scripts/deluge-gtk", "scripts/deluge-tools"],
	py_modules=["dcommon", "deluge", "delugegtk", "dexml"],
	data_files=[("glade", ["glade/delugegtk.glade"])]
	
	)
