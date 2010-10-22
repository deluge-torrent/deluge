import tempfile

import deluge.configmanager
import deluge.log

deluge.log.setupLogger("none")

def set_tmp_config_dir():
    config_directory = tempfile.mkdtemp()
    deluge.configmanager.set_config_dir(config_directory)
    return config_directory

import gettext
import locale
import pkg_resources

# Initialize gettext
try:
    locale.setlocale(locale.LC_ALL, '')
    if hasattr(locale, "bindtextdomain"):
        locale.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
    if hasattr(locale, "textdomain"):
        locale.textdomain("deluge")
    gettext.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
    gettext.textdomain("deluge")
    gettext.install("deluge", pkg_resources.resource_filename("deluge", "i18n"))
except Exception, e:
    print e
