#
# Makefile for Deluge
#
PYVER=`python -c "import sys; print sys.version[:3]"`
PREFIX ?= /usr
DESTDIR ?= ./

all:
	python setup.py build

tarball:
	python setup.py sdist
	mv dist/deluge-*.tar.gz $(DESTDIR)

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
