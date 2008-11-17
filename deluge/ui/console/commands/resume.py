#!/usr/bin/env python
from deluge.ui.console.main import BaseCommand, match_torrents
from deluge.ui.console import mapping
from deluge.ui.client import aclient as client
from deluge.ui.console.colors import templates, default_style as style

class Command(BaseCommand):
    """Resume a torrent"""
    usage = "Usage: resume [ all | <torrent-id> [<torrent-id> ...] ]"
    def handle(self, *args, **options):
        if len(args) == 0:
            print self.usage
            return
        if len(args) == 1 and args[0] == 'all':
            args = tuple() # empty tuple means everything
        try:
            args = mapping.to_ids(args)
            torrents = match_torrents(args)
            client.resume_torrent(torrents)
        except Exception, msg:
            print templates.ERROR(str(msg))
        else:
            print templates.SUCCESS('torrent%s successfully resumed' % ('s' if len(args) > 1 else ''))

    def complete(self, text, *args):
        torrents = match_torrents()
        names = mapping.get_names(torrents)
        return [ x[1] for x in names if x[1].startswith(text) ]

