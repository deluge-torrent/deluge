#!/usr/bin/env python
#
# colors.py
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
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
import re, sys

def color(string, fg=None, attrs=[], bg=None, keep_open=False, input=False):
    if isinstance(attrs, basestring):
        attrs = [attrs]
    attrs = map(str.lower, attrs)
    ansi_reset = "\x1b[0m"
    if input:
        ansi_reset = '\001'+ansi_reset+'\002'
    if len(attrs) == 1 and 'reset' in attrs:
        return ansi_reset
    colors = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
    attributes = ['reset', 'bright', 'dim', None, 'underscore', 'blink', 'reverse', 'hidden']
    _fg = 30 + colors.index(fg.lower()) if fg and fg.lower() in colors else None
    _bg = 40 + colors.index(bg.lower()) if bg and bg.lower() in colors else None
    _attrs = [ str(attributes.index(a)) for a in attrs if a in attributes]
    color_vals = map(str, filter(lambda x: x is not None, [_fg, _bg]))
    color_vals.extend(_attrs)
    reset_cmd = ansi_reset if not keep_open else ''
    color_code = '\x1b['+';'.join(color_vals)+'m'
    if input:
        color_code = '\001'+color_code+'\002'
    return color_code+string+reset_cmd

def make_style(*args, **kwargs):
    return lambda text: color(text, *args, **kwargs)

default_style = {
    'black' : make_style(fg='black'),
    'red' : make_style(fg='red'),
    'green' : make_style(fg='green'),
    'yellow' : make_style(fg='yellow'),
    'blue' : make_style(fg='blue'),
    'magenta' : make_style(fg='magenta'),
    'cyan' : make_style(fg='cyan'),
    'white' : make_style(fg='white'),

    'bold_black' : make_style(fg='black', attrs='bright'),
    'bold_red' : make_style(fg='red', attrs='bright'),
    'bold_green' : make_style(fg='green', attrs='bright'),
    'bold_yellow' : make_style(fg='yellow', attrs='bright'),
    'bold_blue' : make_style(fg='blue', attrs='bright'),
    'bold_magenta' : make_style(fg='magenta', attrs='bright'),
    'bold_cyan' : make_style(fg='cyan', attrs='bright'),
    'bold_white' : make_style(fg='white', attrs='bright'),
}

class Template(str):
    regex = re.compile(r'{{\s*(?P<style>.*?)\((?P<arg>.*?)\)\s*}}')
    style = default_style
    def __new__(self, text):
        return str.__new__(self, Template.regex.sub(lambda mo: Template.style[mo.group('style')](mo.group('arg')), text))

    def __call__(self, *args, **kwargs):
        if kwargs:
            return str(self) % kwargs
        else:
            return str(self) % args

class InputTemplate(Template):
    """This class is similar to Template, but the escapes are wrapped in \001
       and \002 so that readline can properly know the length of each line and
       can wrap lines accordingly.  Use this class for any colored text which
       needs to be used in input prompts, such as in calls to raw_input()."""
    input_codes = re.compile('(\x1b\[.*?m)')
    def __new__(self, text):
        regular_string = InputTemplate.regex.sub(lambda mo: InputTemplate.style[mo.group('style')](mo.group('arg')) , text)
        return str.__new__(self, InputTemplate.input_codes.sub(r'\001\1\002', regular_string))

class struct(object):
    pass

templates = struct()
templates.prompt = InputTemplate('{{bold_white(%s)}}')
templates.ERROR = Template('{{bold_red( * %s)}}')
templates.SUCCESS = Template('{{bold_green( * %s)}}')
templates.help = Template(' * {{bold_blue(%-*s)}} %s')
templates.info_general = Template('{{bold_blue(*** %s:)}} %s')
templates.info_transfers = Template('{{bold_green(*** %s:)}} %s')
templates.info_network = Template('{{bold_white(*** %s:)}} %s')
templates.info_files_header = Template('{{bold_cyan(*** %s:)}}')
templates.info_peers_header = Template('{{bold_magenta(*** %s:)}}')
templates.info_peers = Template('\t * {{bold_blue(%-22s)}} {{bold_green(%-25s)}} {{bold_cyan(Up: %-12s)}} {{bold_magenta(Down: %-12s)}}')
templates.config_display = Template(' * {{bold_blue(%s)}}: %s')
