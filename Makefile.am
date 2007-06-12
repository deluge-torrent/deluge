SUBDIRS = src
dist_doc_DATA = README README.Packagers

CLEANFILES = 

bin_SCRIPTS = deluge
CLEANFILES += deluge

EXTRA_DIST = 

deluge: deluge.in
	sed -e s!\@PYTHON\@!@PYTHON@!		\
	    -e s!\@PYOPTIONS\@!-OOt!		\
	    -e s!\@VERSION\@!${VERSION}!		\
	    < $< > $@

EXTRA_DIST += deluge.in

