#
# Makefile for Deluge
#

PREFIX = /usr


all:
	python setup.py build

install:
	python setup.py install --prefix=$(PREFIX)

clean:
	python setup.py clean; rm -rf ./build
