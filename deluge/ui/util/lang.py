# -*- coding: utf-8 -*-
#
# Copyright (C) 2007,2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import gettext
import locale
import logging
import os
import sys

import deluge.common

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())  # Silence: No handlers could be found for logger "deluge.util.lang"


def set_dummy_trans(warn_msg=None):
    import __builtin__

    def _func(*txt):
        if warn_msg:
            log.warn("'%s' has been marked for translation, but translation is unavailable.", txt[0])
        return txt[0]
    __builtin__.__dict__['_'] = _func
    __builtin__.__dict__['_n'] = _func


def get_translations_path():
    """Get the absolute path to the directory containing translation files"""
    return deluge.common.resource_filename('deluge', 'i18n')


def get_languages():
    from deluge.ui import languages  # Import here so that gettext has been setup first

    lang = []

    translations_path = get_translations_path()
    for root, dirs, files in os.walk(translations_path):
        # Get the dirs
        lang_dirs = dirs
        break
    else:
        return lang

    for i, lang_code in enumerate(lang_dirs):
        name = '%s (Language name missing)' % lang_code
        if lang_code in languages.LANGUAGES:
            name = languages.LANGUAGES[lang_code]
        lang.append([lang_code, name])

    lang = sorted(lang, key=lambda l: l[1])
    return lang


def set_language(lang):
    """
    Set the language to use.

    gettext and GtkBuilder will load the translations from the specified
    language.

    :param lang: the language, e.g. "en", "de" or "en_GB"
    :type lang: str
    """
    lang = str(lang)
    # Necessary to set these environment variables for GtkBuilder
    deluge.common.set_env_variable('LANGUAGE', lang)  # Windows/Linux
    deluge.common.set_env_variable('LANG', lang)  # For OSX

    translations_path = get_translations_path()
    try:
        ro = gettext.translation('deluge', localedir=translations_path, languages=[lang])
        ro.install()
    except IOError as ex:
        log.warn('IOError when loading translations: %s', ex)


# Initialize gettext
def setup_translations(setup_gettext=True, setup_pygtk=False):
    translations_path = get_translations_path()
    domain = 'deluge'
    log.info('Setting up translations from %s', translations_path)

    if setup_pygtk:
        try:
            log.info('Setting up GTK translations from %s', translations_path)

            if deluge.common.windows_check():
                import ctypes
                try:
                    libintl = ctypes.cdll.intl
                except WindowsError:
                    # Fallback to named dll.
                    libintl = ctypes.cdll.LoadLibrary('libintl-8.dll')

                libintl.bindtextdomain(domain, translations_path.encode(sys.getfilesystemencoding()))
                libintl.textdomain(domain)
                libintl.bind_textdomain_codeset(domain, 'UTF-8')
                libintl.gettext.restype = ctypes.c_char_p

            # Use glade for plugins that still uses it
            import gtk
            import gtk.glade
            gtk.glade.bindtextdomain(domain, translations_path)
            gtk.glade.textdomain(domain)
        except Exception as ex:
            log.warning('Unable to initialize glade translations: %s', ex)
    if setup_gettext:
        try:
            if hasattr(locale, 'bindtextdomain'):
                locale.bindtextdomain(domain, translations_path)
            if hasattr(locale, 'textdomain'):
                locale.textdomain(domain)

            gettext.bindtextdomain(domain, translations_path)
            gettext.bind_textdomain_codeset(domain, 'UTF-8')
            gettext.textdomain(domain)
            gettext.install(domain, translations_path, unicode=True)
            import __builtin__
            __builtin__.__dict__['_n'] = gettext.ngettext
        except Exception as ex:
            log.error('Unable to initialize gettext/locale!')
            log.exception(ex)
            set_dummy_trans()

        deluge.common.translate_size_units()
