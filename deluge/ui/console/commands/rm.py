#!/usr/bin/env python
from deluge.ui.console.main import BaseCommand, match_torrents
from deluge.ui.console import mapping
from deluge.ui.console.colors import templates
from deluge.ui.client import aclient as client
from optparse import make_option
import os

class Command(BaseCommand):
    """Remove a torrent"""
    usage = "Usage: rm <torrent-id>"
    aliases = ['del']

    option_list = BaseCommand.option_list + (
            make_option('--remove_torrent', action='store_true', default=False,
                        help="remove the torrent's file"),
            make_option('--remove_data', action='store_true', default=False,
                        help="remove the torrent's data"),
    )

    def handle(self, *args, **options):
        try:
            args = mapping.to_ids(args)
            torrents = match_torrents(args)
            client.remove_torrent(torrents, options['remove_torrent'], options['remove_data'])
        except Exception, msg:
            print template.ERROR(str(msg))

    def complete(self, text, *args):
        torrents = match_torrents()
        names = mapping.get_names(torrents)
        return [ x[1] for x in names if x[1].startswith(text) ]
