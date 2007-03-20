# $Id: Makefile,v 1.21 2007/03/02 10:45:52 nanard Exp $
# MiniUPnP Project
# http://miniupnp.free.fr/
# (c) 2005-2006 Thomas Bernard
CC = gcc
#AR = gar
CFLAGS = -O -Wall -g -DDEBUG
#CFLAGS = -O -Wall -DNDEBUG
INSTALL = install
#following libs are needed on Solaris
#LDLIBS=-lsocket -lnsl -lresolv

SRCS = igd_desc_parse.c miniupnpc.c minixml.c minisoap.c miniwget.c \
       upnpc.c upnpcommands.c upnpreplyparse.c testminixml.c \
	   minixmlvalid.c

OBJS = $(patsubst %.c,%.o,$(SRCS))

# HEADERS to install
HEADERS = miniupnpc.h miniwget.h upnpcommands.h igd_desc_parse.h \
          upnpreplyparse.h
LIBRARY = libminiupnpc.a
EXECUTABLES = upnpc testminixml minixmlvalid

INSTALLPREFIX = /usr
INSTALLDIRINC = $(INSTALLPREFIX)/include/miniupnpc
INSTALLDIRLIB = $(INSTALLPREFIX)/lib

.PHONY:	install clean depend all

all:	validateminixml $(LIBRARY) $(EXECUTABLES)

validateminixml:	minixmlvalid
	@echo "minixml validation test"
	./minixmlvalid
	touch $@

clean:
		$(RM) $(LIBRARY) $(EXECUTABLES) $(OBJS)

install:	$(LIBRARY)
	$(INSTALL) -d $(INSTALLDIRINC)
	$(INSTALL) --mode=644 $(HEADERS) $(INSTALLDIRINC)
	$(INSTALL) --mode=644 $(LIBRARY) $(INSTALLDIRLIB)

cleaninstall:
	$(RM) -r $(INSTALLDIRINC)
	$(RM) $(INSTALLDIRLIB)/$(LIBRARY)

depend:
	makedepend -Y -- $(CFLAGS) -- $(SRCS) 2>/dev/null

libminiupnpc.a:	miniwget.o minixml.o igd_desc_parse.o minisoap.o miniupnpc.o upnpreplyparse.o upnpcommands.o
	$(AR) crs $@ $?

upnpc:	upnpc.o libminiupnpc.a

testminixml:	minixml.o igd_desc_parse.o testminixml.o

minixmlvalid:	minixml.o minixmlvalid.o

# DO NOT DELETE THIS LINE -- make depend depends on it.

igd_desc_parse.o: igd_desc_parse.h
miniupnpc.o: miniupnpc.h declspec.h igd_desc_parse.h miniwget.h minisoap.h
miniupnpc.o: minixml.h upnpcommands.h upnpreplyparse.h
minixml.o: minixml.h
minisoap.o: minisoap.h
miniwget.o: miniupnpc.h declspec.h igd_desc_parse.h
upnpc.o: miniwget.h declspec.h miniupnpc.h igd_desc_parse.h upnpcommands.h
upnpc.o: upnpreplyparse.h
upnpcommands.o: upnpcommands.h upnpreplyparse.h miniupnpc.h declspec.h
upnpcommands.o: igd_desc_parse.h
upnpreplyparse.o: upnpreplyparse.h minixml.h
testminixml.o: minixml.h igd_desc_parse.h
minixmlvalid.o: minixml.h
