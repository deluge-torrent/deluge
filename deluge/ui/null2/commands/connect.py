#!/usr/bin/env python
from deluge.ui.null2.main import BaseCommand
from deluge.ui.null2.colors import templates, default_style as style
from deluge.ui.client import aclient as client

class Command(BaseCommand):
    """Connect to a new deluge server."""
    def handle(self, host='localhost', port='58846', **options):
        port = int(port)
        if host[:7] != "http://":
            host = "http://" + host
        client.set_core_uri("%s:%d" % (host, port))
        print templates.SUCCESS('connected to %s:%d' % (host, port))
