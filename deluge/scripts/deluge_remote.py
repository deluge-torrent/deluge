#!/usr/bin/python
#
# This software is in the public domain, furnished "as is", without technical
# support, and with no warranty, express or implied, as to its usefulness for
# any purpose.
#
# deluge_config.py
# This code (at least in theory) allows one to alter configuration settings
# on a deluge backend.   At the moment, though, it only alters the parameters
# that I've found useful to change.
#
# Authour: Garett Harnish

import logging
import sys
from optparse import OptionParser


def is_float_digit(string):
    if string.isdigit():
        return True
    else:
        try:
            float(string)
            return True
        except ValueError:
            return False


# set up command-line options
parser = OptionParser()
parser.add_option(
    '--port',
    help='port for deluge backend host (default: 58846)',
    default='58846',
    dest='port',
)
parser.add_option(
    '--host',
    help='hostname of deluge backend to connect to (default: localhost)',
    default='localhost',
    dest='host',
)
parser.add_option(
    '--max_active_limit',
    dest='max_active_limit',
    help='sets the absolute maximum number of active torrents on the deluge backend',
)
parser.add_option(
    '--max_active_downloading',
    dest='max_active_downloading',
    help='sets the maximum number of active downloading torrents on the deluge backend',
)
parser.add_option(
    '--max_active_seeding',
    dest='max_active_seeding',
    help='sets the maximum number of active seeding torrents on the deluge backend',
)
parser.add_option(
    '--max_download_speed',
    help='sets the maximum global download speed on the deluge backend',
    dest='max_download_speed',
)
parser.add_option(
    '--max_upload_speed',
    help='sets the maximum global upload speed on the deluge backend',
    dest='max_upload_speed',
)
parser.add_option(
    '--debug',
    help='outputs debug information to the console',
    default=False,
    action='store_true',
    dest='debug',
)

# grab command-line options
(options, args) = parser.parse_args()

if not options.debug:
    logging.disable(logging.ERROR)

settings = {}

# set values if set and valid
if options.max_active_limit:
    if options.max_active_limit.isdigit() and int(options.max_active_limit) >= 0:
        settings['max_active_limit'] = int(options.max_active_limit)
    else:
        sys.stderr.write('ERROR: Invalid max_active_limit parameter!\n')
        sys.exit(-1)

if options.max_active_downloading:
    if (
        options.max_active_downloading.isdigit()
        and int(options.max_active_downloading) >= 0
    ):
        settings['max_active_downloading'] = int(options.max_active_downloading)
    else:
        sys.stderr.write('ERROR: Invalid max_active_downloading parameter!\n')
        sys.exit(-1)

if options.max_active_seeding:
    if options.max_active_seeding.isdigit() and int(options.max_active_seeding) >= 0:
        settings['max_active_seeding'] = int(options.max_active_seeding)
    else:
        sys.stderr.write('ERROR: Invalid max_active_seeding parameter!\n')
        sys.exit(-1)

if options.max_download_speed:
    if is_float_digit(options.max_download_speed) and (
        float(options.max_download_speed) >= 0.0
        or float(options.max_download_speed) == -1.0
    ):
        settings['max_download_speed'] = float(options.max_download_speed)
    else:
        sys.stderr.write('ERROR: Invalid max_download_speed parameter!\n')
        sys.exit(-1)

if options.max_upload_speed:
    if is_float_digit(options.max_upload_speed) and (
        float(options.max_upload_speed) >= 0.0
        or float(options.max_upload_speed) == -1.0
    ):
        settings['max_upload_speed'] = float(options.max_upload_speed)
    else:
        sys.stderr.write('ERROR: Invalid max_upload_speed parameter!\n')
        sys.exit(-1)

# If there is something to do ...
if settings:
    # create connection to daemon
    from deluge.ui.client import sclient as client

    client.set_core_uri('http://' + options.host + ':' + options.port)

    # commit configurations changes
    client.set_config(settings)
