from __future__ import unicode_literals

from deluge.ui.web.web import Web


def start():
    web = Web()
    web.start()
