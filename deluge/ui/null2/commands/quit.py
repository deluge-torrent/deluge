#!/usr/bin/env python
from deluge.ui.client import aclient as client
from deluge.ui.null2.main import BaseCommand

class Command(BaseCommand):
    """Exit from the client."""
    aliases = ['exit']
    def handle(self, *args, **options):
        print "Thanks!"
        raise StopIteration

