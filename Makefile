#
# Makefile for Deluge
#
PYVER=`python -c "import sys; print sys.version[:3]"`
PREFIX = /usr

all:
	python setup.py build

install:
	python setup.py install --prefix=$(PREFIX)

clean:
	python setup.py clean
	rm -rf ./build
	rm msgfmt.pyc
	find . -name *.pyc -exec rm {} \;

uninstall:
	-rm $(PREFIX)/bin/deluge
	-rm -r $(PREFIX)/lib/python${PYVER}/site-packages/deluge
	-rm -r $(PREFIX)/lib/python${PYVER}/site-packages/deluge-*.egg-info
	-rm -r $(PREFIX)/share/deluge
	-find ${PREFIX}/share/locale -name deluge.mo -exec rm {} \;
	-rm $(PREFIX)/share/applications/deluge.desktop
	-rm $(PREFIX)/share/pixmaps/deluge.png
