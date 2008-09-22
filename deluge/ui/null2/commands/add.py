#!/usr/bin/env python
from deluge.ui.null2.main import BaseCommand, match_torrents
from deluge.ui.null2 import mapping
from deluge.ui.null2.colors import templates
from deluge.ui.client import aclient as client
from optparse import make_option
import os

class Command(BaseCommand):
    """Add a torrent"""
    option_list = BaseCommand.option_list + (
            make_option('-p', '--path', dest='path',
                        help='save path for torrent'),
    )

    usage = "Usage: add [-p <save-location>] <torrent-file> [<torrent-file> ...]"

    def handle(self, *args, **options):
        if options['path'] is None:
            def _got_config(configs):
                global save_path
                save_path = configs['download_location']
            client.get_config(_got_config)
            client.force_call()
            options['path'] = save_path
        else:
            client.set_config({'download_location': options['path']})
        if not options['path']:
            print templates.ERROR("There's no save-path specified. You must specify a path to save the downloaded files.")
            return
        try:
            client.add_torrent_file(args)
        except Exception, msg:
            print templates.ERROR("Error: %s" % str(msg))
