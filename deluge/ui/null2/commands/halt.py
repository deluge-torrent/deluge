#!/usr/bin/env python
from deluge.ui.null2.main import BaseCommand, match_torrents
from deluge.ui.null2 import mapping
from deluge.ui.null2.colors import templates
from deluge.ui.client import aclient as client

class Command(BaseCommand):
    "Shutdown the deluge server."
    def handle(self, **options):
        client.shutdown()
