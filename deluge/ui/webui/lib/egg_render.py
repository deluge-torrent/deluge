#!/usr/bin/env python
#(c) Martijn Voncken, mvoncken@gmail.com
#Same Licence as web.py 0.22
"""
render object for web.py
renders from egg instead of directory.
"""
from web import template
import pkg_resources
import os


class egg_render:
    """
    templates directly from an egg
    """
    def __init__(self, resource, base_path , cache=False):
        self.resource = resource
        self.base_path = base_path
        self.cache = cache

    def __getattr__(self, attr):
        filename  = attr + ".html" #<--bug, not consistent with the web.py renderer, that renderer ignores extensions.
        template_data = pkg_resources.resource_string(self.resource, os.path.join(self.base_path, filename))
        c = template.Template(template_data, filename = filename)
        if self.cache:
            setattr(self, attr, c)
        return c


if __name__ == '__main__':
    #example:
    pass
