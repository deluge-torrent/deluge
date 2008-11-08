#!/usr/bin/env python
from deluge.ui.console import UI_PATH
from deluge.ui.console.main import BaseCommand, load_commands
from deluge.ui.console.colors import templates
import os

class Command(BaseCommand):
    """displays help on other commands"""

    usage =  "Usage: help [command]"

    def __init__(self):
        BaseCommand.__init__(self)
        # get a list of commands, exclude 'help' so we won't run into a recursive loop.
        self._commands = load_commands(os.path.join(UI_PATH,'commands'), exclude=['help'])
        self._commands['help'] = self
        
    def handle(self, *args, **options):
        if args:
            if len(args) > 1:
                print usage
                return
            try:
                cmd = self._commands[args[0]]
            except KeyError:
                print templates.ERROR('unknown command %r' % args[0])
                return 
            try:
                parser = cmd.create_parser()
                print parser.format_help()
            except AttributeError, e:
                print cmd.__doc__ or 'No help for this command'
        else:
            max_length = max( len(k) for k in self._commands)
            for cmd in sorted(self._commands):
                print templates.help(max_length, cmd, self._commands[cmd].__doc__ or '')
            print 
            print 'for help on a specific command, use "<command> --help"'
    
    def complete(self, text, *args):
        return [ x for x in self._commands.keys() if x.startswith(text) ]
