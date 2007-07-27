import gettext
import locale
import os

from common import INSTALL_PREFIX

APP = 'deluge'
DIR = os.path.join(INSTALL_PREFIX, 'share', 'locale')
locale.setlocale(locale.LC_ALL, '')
locale.bindtextdomain(APP, DIR)
locale.textdomain(APP)
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
gettext.install(APP, DIR)
