# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


from __future__ import unicode_literals


class DelugeError(Exception):
    def __new__(cls, *args, **kwargs):
        inst = super(DelugeError, cls).__new__(cls, *args, **kwargs)
        inst._args = args
        inst._kwargs = kwargs
        return inst

    def __init__(self, message=None):
        super(DelugeError, self).__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class DaemonRunningError(DelugeError):
    pass


class InvalidTorrentError(DelugeError):
    pass


class AddTorrentError(DelugeError):
    pass


class InvalidPathError(DelugeError):
    pass


class WrappedException(DelugeError):
    def __init__(self, message, exception_type, traceback):
        super(WrappedException, self).__init__(message)
        self.type = exception_type
        self.traceback = traceback

    def __str__(self):
        return '%s\n%s' % (self.message, self.traceback)


class _ClientSideRecreateError(DelugeError):
    pass


class IncompatibleClient(_ClientSideRecreateError):
    def __init__(self, daemon_version):
        self.daemon_version = daemon_version
        msg = (
            'Your deluge client is not compatible with the daemon. '
            'Please upgrade your client to %(daemon_version)s'
        ) % {'daemon_version': self.daemon_version}
        super(IncompatibleClient, self).__init__(message=msg)


class NotAuthorizedError(_ClientSideRecreateError):
    def __init__(self, current_level, required_level):
        msg = ('Auth level too low: %(current_level)s < %(required_level)s') % {
            'current_level': current_level,
            'required_level': required_level,
        }
        super(NotAuthorizedError, self).__init__(message=msg)
        self.current_level = current_level
        self.required_level = required_level


class _UsernameBasedPasstroughError(_ClientSideRecreateError):
    def __init__(self, message, username):
        super(_UsernameBasedPasstroughError, self).__init__(message)
        self.username = username


class BadLoginError(_UsernameBasedPasstroughError):
    pass


class AuthenticationRequired(_UsernameBasedPasstroughError):
    pass


class AuthManagerError(_UsernameBasedPasstroughError):
    pass


class LibtorrentImportError(ImportError):
    pass
