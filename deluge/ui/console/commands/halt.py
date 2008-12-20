#!/usr/bin/env python
from deluge.ui.console.main import BaseCommand, match_torrents
from deluge.ui.console import mapping
from deluge.ui.console.colors import templates
from deluge.ui.client import aclient as client

class Command(BaseCommand):
    "Shutdown the deluge server."
    def handle(self, **options):
        client.daemon.shutdown(None)
