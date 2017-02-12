# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import re

from deluge.ui.console.utils import format_utils

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)

colors = [
    'COLOR_BLACK',
    'COLOR_BLUE',
    'COLOR_CYAN',
    'COLOR_GREEN',
    'COLOR_MAGENTA',
    'COLOR_RED',
    'COLOR_WHITE',
    'COLOR_YELLOW'
]

# {(fg, bg): pair_number, ...}
color_pairs = {
    ('white', 'black'): 0  # Special case, can't be changed
}

# Some default color schemes
schemes = {
    'input': ('white', 'black'),
    'normal': ('white', 'black'),
    'status': ('yellow', 'blue', 'bold'),
    'info': ('white', 'black', 'bold'),
    'error': ('red', 'black', 'bold'),
    'success': ('green', 'black', 'bold'),
    'event': ('magenta', 'black', 'bold'),
    'selected': ('black', 'white', 'bold'),
    'marked': ('white', 'blue', 'bold'),
    'selectedmarked': ('blue', 'white', 'bold'),
    'header': ('green', 'black', 'bold'),
    'filterstatus': ('green', 'blue', 'bold')
}

# Colors for various torrent states
state_color = {
    'Seeding': '{!blue,black,bold!}',
    'Downloading': '{!green,black,bold!}',
    'Paused': '{!white,black!}',
    'Checking': '{!green,black!}',
    'Queued': '{!yellow,black!}',
    'Error': '{!red,black,bold!}',
    'Moving': '{!green,black,bold!}'
}

type_color = {
    bool: '{!yellow,black,bold!}',
    int: '{!green,black,bold!}',
    float: '{!green,black,bold!}',
    str: '{!cyan,black,bold!}',
    list: '{!magenta,black,bold!}',
    dict: '{!white,black,bold!}'
}


def get_color_pair(fg, bg):
    return color_pairs[(fg, bg)]


def init_colors():
    curses.start_color()

    # We want to redefine white/black as it makes underlining work for some terminals
    # but can also fail on others, so we try/except

    def define_pair(counter, fg_name, bg_name, fg, bg):
        try:
            curses.init_pair(counter, fg, bg)
            color_pairs[(fg_name, bg_name)] = counter
            counter += 1
        except curses.error as ex:
            log.warn('Error: %s', ex)
        return counter

    # Create the color_pairs dict
    counter = 1
    for fg in colors:
        for bg in colors:
            counter = define_pair(counter, fg[6:].lower(), bg[6:].lower(), getattr(curses, fg), getattr(curses, bg))

    counter = define_pair(counter, 'white', 'grey', curses.COLOR_WHITE, 241)
    counter = define_pair(counter, 'black', 'whitegrey', curses.COLOR_BLACK, 249)
    counter = define_pair(counter, 'magentadark', 'white', 99, curses.COLOR_WHITE)


class BadColorString(Exception):
    pass


def replace_tabs(line):
    """
    Returns a string with tabs replaced with spaces.

    """
    for i in range(line.count('\t')):
        tab_length = 8 - (len(line[:line.find('\t')]) % 8)
        line = line.replace('\t', ' ' * tab_length, 1)
    return line


def strip_colors(line):
    """
    Returns a string with the color formatting removed.

    """
    # Remove all the color tags
    while line.find('{!') != -1:
        line = line[:line.find('{!')] + line[line.find('!}') + 2:]

    return line


def get_line_length(line, encoding='UTF-8'):
    """
    Returns the string length without the color formatting.

    """
    if line.count('{!') != line.count('!}'):
        raise BadColorString('Number of {! is not equal to number of !}')

    if isinstance(line, unicode):
        line = line.encode(encoding, 'replace')

    # Remove all the color tags
    line = strip_colors(line)

    # Replace tabs with the appropriate amount of spaces
    line = replace_tabs(line)
    return len(line)


def get_line_width(line, encoding='UTF-8'):
    """
    Get width of string considering double width characters

    """
    if line.count('{!') != line.count('!}'):
        raise BadColorString('Number of {! is not equal to number of !}')

    if isinstance(line, unicode):
        line = line.encode(encoding, 'replace')

    # Remove all the color tags
    line = strip_colors(line)

    # Replace tabs with the appropriate amount of spaces
    line = replace_tabs(line)
    return format_utils.strwidth(line)


def parse_color_string(s, encoding='UTF-8'):
    """
    Parses a string and returns a list of 2-tuples (color, string).

    :param s:, string to parse
    :param encoding: the encoding to use on output

    """
    if s.count('{!') != s.count('!}'):
        raise BadColorString('Number of {! is not equal to number of !}')

    if isinstance(s, unicode):
        s = s.encode(encoding, 'replace')

    ret = []
    last_color_attr = None
    # Keep track of where the strings
    while s.find('{!') != -1:
        begin = s.find('{!')
        if begin > 0:
            ret.append((curses.color_pair(color_pairs[(schemes['input'][0], schemes['input'][1])]), s[:begin]))

        end = s.find('!}')
        if end == -1:
            raise BadColorString('Missing closing "!}"')

        # Get a list of attributes in the bracketed section
        attrs = s[begin + 2:end].split(',')

        if len(attrs) == 1 and not attrs[0].strip(' '):
            raise BadColorString('No description in {! !}')

        def apply_attrs(cp, attrs):
            # This function applies any additional attributes as necessary
            for attr in attrs:
                if attr == 'ignore':
                    continue
                mode = '+'
                if attr[0] in ['+', '-']:
                    mode = attr[0]
                    attr = attr[1:]
                if mode == '+':
                    cp |= getattr(curses, 'A_' + attr.upper())
                else:
                    cp ^= getattr(curses, 'A_' + attr.upper())
            return cp

        # Check for a builtin type first
        if attrs[0] in schemes:
            pair = (schemes[attrs[0]][0], schemes[attrs[0]][1])
            if pair not in color_pairs:
                log.debug('Color pair does not exist: %s, attrs: %s', pair, attrs)
                pair = ('white', 'black')
            # Get the color pair number
            color_pair = curses.color_pair(color_pairs[pair])
            color_pair = apply_attrs(color_pair, schemes[attrs[0]][2:])
            last_color_attr = color_pair
        else:
            attrlist = ['blink', 'bold', 'dim', 'reverse', 'standout', 'underline']

            if attrs[0][0] in ['+', '-']:
                # Color is not given, so use last color
                if last_color_attr is None:
                    raise BadColorString('No color value given when no previous color was used!: %s' % (attrs[0]))
                color_pair = last_color_attr
                for i, attr in enumerate(attrs):
                    if attr[1:] not in attrlist:
                        raise BadColorString('Bad attribute value!: %s' % (attr))
            else:
                # This is a custom color scheme
                fg = attrs[0]
                bg = 'black'  # Default to 'black' if no bg is chosen
                if len(attrs) > 1:
                    bg = attrs[1]
                try:
                    pair = (fg, bg)
                    if pair not in color_pairs:
                        # Color pair missing, this could be because the
                        # terminal settings allows no colors. If background is white, we
                        # assume this means selection, and use "white", "black" + reverse
                        # To have white background and black foreground
                        log.debug('Color pair does not exist: %s', pair)
                        if pair[1] == 'white':
                            if attrs[2] == 'ignore':
                                attrs[2] = 'reverse'
                            else:
                                attrs.append('reverse')
                        pair = ('white', 'black')
                    color_pair = curses.color_pair(color_pairs[pair])
                    last_color_attr = color_pair
                    attrs = attrs[2:]  # Remove colors
                except KeyError:
                    raise BadColorString('Bad color value in tag: %s,%s' % (fg, bg))
            # Check for additional attributes and OR them to the color_pair
            color_pair = apply_attrs(color_pair, attrs)
            last_color_attr = color_pair
        # We need to find the text now, so lets try to find another {! and if
        # there isn't one, then it's the rest of the string
        next_begin = s.find('{!', end)

        if next_begin == -1:
            ret.append((color_pair, replace_tabs(s[end + 2:])))
            break
        else:
            ret.append((color_pair, replace_tabs(s[end + 2:next_begin])))
            s = s[next_begin:]

    if not ret:
        # There was no color scheme so we add it with a 0 for white on black
        ret = [(0, s)]
    return ret


class ConsoleColorFormatter(object):
    """
    Format help in a way suited to deluge CmdLine mode - colors, format, indentation...
    """

    replace_dict = {
        '<torrent-id>': '{!green!}%s{!input!}',
        '<torrent>': '{!green!}%s{!input!}',
        '<command>': '{!green!}%s{!input!}',

        '<state>': '{!yellow!}%s{!input!}',
        '\\.\\.\\.': '{!yellow!}%s{!input!}',
        '\\s\\*\\s': '{!blue!}%s{!input!}',
        '(?<![\\-a-z])(-[a-zA-Z0-9])': '{!red!}%s{!input!}',
        # "(\-[a-zA-Z0-9])": "{!red!}%s{!input!}",
        '--[_\\-a-zA-Z0-9]+': '{!green!}%s{!input!}',
        '(\\[|\\])': '{!info!}%s{!input!}',

        '<tab>': '{!white!}%s{!input!}',
        '[_A-Z]{3,}': '{!cyan!}%s{!input!}',
        '<key>': '{!cyan!}%s{!input!}',
        '<value>': '{!cyan!}%s{!input!}',
        'usage:': '{!info!}%s{!input!}',
        '<download-folder>': '{!yellow!}%s{!input!}',
        '<torrent-file>': '{!green!}%s{!input!}'

    }

    def format_colors(self, string):
        def r(repl):
            return lambda s: repl % s.group()
        for key, replacement in self.replace_dict.items():
            string = re.sub(key, r(replacement), string)
        return string
