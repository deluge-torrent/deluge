#
# colors.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#

try:
    import curses
except ImportError:
    pass

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
    ("white", "black"): 0 # Special case, can't be changed
}

# Some default color schemes
schemes = {
    "input": ("white", "black"),
    "status": ("yellow", "blue", "bold"),
    "info": ("white", "black", "bold"),
    "error": ("red", "black", "bold"),
    "success": ("green", "black", "bold"),
    "event": ("magenta", "black", "bold")
}

# Colors for various torrent states
state_color = {
    "Seeding": "{!blue,black,bold!}",
    "Downloading": "{!green,black,bold!}",
    "Paused": "{!white,black!}",
    "Checking": "{!green,black!}",
    "Queued": "{!yellow,black!}",
    "Error": "{!red,black,bold!}"
}

type_color = {
    bool: "{!yellow,black,bold!}",
    int: "{!green,black,bold!}",
    float: "{!green,black,bold!}",
    str: "{!cyan,black,bold!}",
    list: "{!magenta,black,bold!}",
    dict: "{!white,black,bold!}"
}

def init_colors():
    # Create the color_pairs dict
    counter = 1
    for fg in colors:
        for bg in colors:
            if fg == "COLOR_WHITE" and bg == "COLOR_BLACK":
                continue
            color_pairs[(fg[6:].lower(), bg[6:].lower())] = counter
            curses.init_pair(counter, getattr(curses, fg), getattr(curses, bg))
            counter += 1

class BadColorString(Exception):
    pass

def replace_tabs(line):
    """
    Returns a string with tabs replaced with spaces.

    """
    for i in range(line.count("\t")):
        tab_length = 8 - (len(line[:line.find("\t")]) % 8)
        line = line.replace("\t", " " * tab_length, 1)
    return line

def strip_colors(line):
    """
    Returns a string with the color formatting removed.

    """
    # Remove all the color tags
    while line.find("{!") != -1:
        line = line[:line.find("{!")] + line[line.find("!}") + 2:]

    return line

def get_line_length(line, encoding="UTF-8"):
    """
    Returns the string length without the color formatting.

    """
    if line.count("{!") != line.count("!}"):
        raise BadColorString("Number of {! is not equal to number of !}")

    if isinstance(line, unicode):
        line = line.encode(encoding, "replace")

    # Remove all the color tags
    line = strip_colors(line)

    # Replace tabs with the appropriate amount of spaces
    line = replace_tabs(line)
    return len(line)

def parse_color_string(s, encoding="UTF-8"):
    """
    Parses a string and returns a list of 2-tuples (color, string).

    :param s:, string to parse
    :param encoding: the encoding to use on output

    """
    if s.count("{!") != s.count("!}"):
        raise BadColorString("Number of {! is not equal to number of !}")

    if isinstance(s, unicode):
        s = s.encode(encoding, "replace")

    ret = []
    # Keep track of where the strings
    col_index = 0
    while s.find("{!") != -1:
        begin = s.find("{!")
        if begin > 0:
            ret.append((curses.color_pair(color_pairs[(schemes["input"][0], schemes["input"][1])]), s[:begin]))

        end = s.find("!}")
        if end == -1:
            raise BadColorString("Missing closing '!}'")

        # Get a list of attributes in the bracketed section
        attrs = s[begin+2:end].split(",")

        if len(attrs) == 1 and not attrs[0].strip(' '):
            raise BadColorString("No description in {! !}")

        def apply_attrs(cp, a):
            # This function applies any additional attributes as necessary
            if len(a) > 2:
                for attr in a[2:]:
                    cp |= getattr(curses, "A_" + attr.upper())
            return cp

        # Check for a builtin type first
        if attrs[0] in schemes:
            # Get the color pair number
            color_pair = curses.color_pair(color_pairs[(schemes[attrs[0]][0], schemes[attrs[0]][1])])
            color_pair = apply_attrs(color_pair, schemes[attrs[0]])

        else:
            # This is a custom color scheme
            fg = attrs[0]
            if len(attrs) > 1:
                bg = attrs[1]
            else:
                # Default to 'black' if no bg is chosen
                bg = "black"

            try:
                color_pair = curses.color_pair(color_pairs[(fg, bg)])
            except KeyError:
                raise BadColorString("Bad color value in tag: %s,%s" % (fg, bg))

            # Check for additional attributes and OR them to the color_pair
            color_pair = apply_attrs(color_pair, attrs)

        # We need to find the text now, so lets try to find another {! and if
        # there isn't one, then it's the rest of the string
        next_begin = s.find("{!", end)

        if next_begin == -1:
            ret.append((color_pair, replace_tabs(s[end+2:])))
            break
        else:
            ret.append((color_pair, replace_tabs(s[end+2:next_begin])))
            s = s[next_begin:]

    if not ret:
        # There was no color scheme so we add it with a 0 for white on black
        ret = [(0, s)]
    return ret
