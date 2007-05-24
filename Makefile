#
# Makefile for Deluge
#

VERSION ?= 0.5.1

PREFIX ?= /usr


all:
	python setup.py build

install:
	python setup.py install --prefix=$(PREFIX)
