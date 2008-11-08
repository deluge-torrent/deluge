#!/usr/bin/env python
from deluge.ui.console.main import BaseCommand
from deluge.ui.client import aclient as client
from deluge.ui.console.colors import templates, default_style as style
import logging

class Command(BaseCommand):
    """Enable and disable debugging"""
    usage = 'debug [on|off]'
    def handle(self, state='', **options):
        if state == 'on':
            logging.disable(logging.DEBUG)
        elif state == 'off':
            logging.disable(logging.ERROR)
        else:
            print templates.ERROR(self.usage)

    def complete(self, text, *args):
        return [ x for x in ['on', 'off'] if x.startswith(text) ]
