# -*- coding: utf-8 -*-
#
# Copyright (C) 2007,2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import ctypes
import gettext
import locale
import logging
import os
import sys

from six.moves import builtins

import deluge.common

log = logging.getLogger(__name__)
log.addHandler(
    logging.NullHandler()
)  # Silence: No handlers could be found for logger "deluge.util.lang"

I18N_DOMAIN = 'deluge'


def set_dummy_trans(warn_msg=None):
    def _func(*txt):
        if warn_msg:
            log.warning(
                '"%s" has been marked for translation, but translation is unavailable.',
                txt[0],
            )
        return txt[0]

    builtins.__dict__['_'] = _func
    builtins.__dict__['ngettext'] = builtins.__dict__['_n'] = _func


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
    # Necessary to set these environment variables for GtkBuilder
    deluge.common.set_env_variable('LANGUAGE', lang)  # Windows/Linux
    deluge.common.set_env_variable('LANG', lang)  # For OSX

    translations_path = get_translations_path()
    try:
        ro = gettext.translation(
            'deluge', localedir=translations_path, languages=[lang]
        )
        ro.install()
    except IOError as ex:
        log.warning('IOError when loading translations: %s', ex)


# Initialize gettext
def setup_translations():
    translations_path = get_translations_path()
    log.info('Setting up translations from %s', translations_path)

    try:
        if hasattr(locale, 'bindtextdomain'):
            locale.bindtextdomain(I18N_DOMAIN, translations_path)
        if hasattr(locale, 'textdomain'):
            locale.textdomain(I18N_DOMAIN)

        gettext.bindtextdomain(I18N_DOMAIN, translations_path)
        gettext.bind_textdomain_codeset(I18N_DOMAIN, 'UTF-8')
        gettext.textdomain(I18N_DOMAIN)

        # Workaround for Python 2 unicode gettext (keyword removed in Py3).
        kwargs = {} if not deluge.common.PY2 else {'unicode': True}

        gettext.install(I18N_DOMAIN, translations_path, names='ngettext', **kwargs)
        builtins.__dict__['_n'] = builtins.__dict__['ngettext']

        libintl = None
        if deluge.common.windows_check():
            libintl = ctypes.cdll.LoadLibrary('libintl-8.dll')
        elif deluge.common.osx_check():
            libintl = ctypes.cdll.LoadLibrary('libintl.dylib')

        if libintl:
            libintl.bindtextdomain(
                I18N_DOMAIN, translations_path.encode(sys.getfilesystemencoding())
            )
            libintl.textdomain(I18N_DOMAIN)
            libintl.bind_textdomain_codeset(I18N_DOMAIN, 'UTF-8')
            libintl.gettext.restype = ctypes.c_char_p

    except Exception as ex:
        log.error('Unable to initialize gettext/locale!')
        log.exception(ex)
        set_dummy_trans()

    deluge.common.translate_size_units()
