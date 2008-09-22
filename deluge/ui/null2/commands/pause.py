#!/usr/bin/env python
from deluge.ui.null2.main import BaseCommand, match_torrents
from deluge.ui.null2 import mapping
from deluge.ui.client import aclient as client
from deluge.ui.null2.colors import templates, default_style as style

class Command(BaseCommand):
    """Pause a torrent"""
    usage = "Usage: pause <torrent-id> [<torrent-id> ...]"
    def handle(self, *args, **options):
        try:
            args = mapping.to_ids(args)
            torrents = match_torrents(args)
            client.pause_torrent(torrents)
        except Exception, msg:
            print templates.ERROR(str(msg))
        else:
            print templates.SUCCESS('torrent%s successfully paused' % ('s' if len(args) > 1 else ''))

    def complete(self, text, *args):
        torrents = match_torrents()
        names = mapping.get_names(torrents)
        return [ x[1] for x in names if x[1].startswith(text) ]
