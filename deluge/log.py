#
# log.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2010 Pedro Algarvio <pedro@algarvio.me>
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

"""Logging functions"""

import os
import inspect
import logging
from deluge import common
from twisted.internet import defer
from twisted.python.log import PythonLoggingObserver

__all__ = ["setupLogger", "setLoggerLevel", "getPluginLogger", "LOG"]

LoggingLoggerClass = logging.getLoggerClass()

if 'dev' in common.get_version():
    DEFAULT_LOGGING_FORMAT = "%%(asctime)s.%%(msecs)03.0f [%%(levelname)-8s][%%(name)-%ds:%%(lineno)-4d] %%(message)s"
else:
    DEFAULT_LOGGING_FORMAT = "%%(asctime)s [%%(levelname)-8s][%%(name)-%ds] %%(message)s"
MAX_LOGGER_NAME_LENGTH = 3

class Logging(LoggingLoggerClass):
    def __init__(self, logger_name):
        LoggingLoggerClass.__init__(self, logger_name)

        # This makes module name padding increase to the biggest module name
        # so that logs keep readability.
        global MAX_LOGGER_NAME_LENGTH
        if len(logger_name) > MAX_LOGGER_NAME_LENGTH:
            MAX_LOGGER_NAME_LENGTH = len(logger_name)
            for handler in logging.getLogger().handlers:
                handler.setFormatter(logging.Formatter(
                    DEFAULT_LOGGING_FORMAT % MAX_LOGGER_NAME_LENGTH,
                    datefmt="%H:%M:%S"
                ))

    @defer.inlineCallbacks
    def garbage(self, msg, *args, **kwargs):
        yield LoggingLoggerClass.log(self, 1, msg, *args, **kwargs)

    @defer.inlineCallbacks
    def trace(self, msg, *args, **kwargs):
        yield LoggingLoggerClass.log(self, 5, msg, *args, **kwargs)

    @defer.inlineCallbacks
    def debug(self, msg, *args, **kwargs):
        yield LoggingLoggerClass.debug(self, msg, *args, **kwargs)

    @defer.inlineCallbacks
    def info(self, msg, *args, **kwargs):
        yield LoggingLoggerClass.info(self, msg, *args, **kwargs)

    @defer.inlineCallbacks
    def warning(self, msg, *args, **kwargs):
        yield LoggingLoggerClass.warning(self, msg, *args, **kwargs)

    warn = warning

    @defer.inlineCallbacks
    def error(self, msg, *args, **kwargs):
        yield LoggingLoggerClass.error(self, msg, *args, **kwargs)

    @defer.inlineCallbacks
    def critical(self, msg, *args, **kwargs):
        yield LoggingLoggerClass.critical(self, msg, *args, **kwargs)

    @defer.inlineCallbacks
    def exception(self, msg, *args, **kwargs):
        yield LoggingLoggerClass.exception(self, msg, *args, **kwargs)

    def findCaller(self):
        f = logging.currentframe().f_back
        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename in (__file__.replace('.pyc', '.py'),
                            defer.__file__.replace('.pyc', '.py')):
                f = f.f_back
                continue
            rv = (filename, f.f_lineno, co.co_name)
            break
        return rv

levels = {
    "none": logging.NOTSET,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "none": logging.CRITICAL,
    "debug": logging.DEBUG,
    "trace": 5,
    "garbage": 1
}


def setupLogger(level="error", filename=None, filemode="w"):
    """
    Sets up the basic logger and if `:param:filename` is set, then it will log
    to that file instead of stdout.

    :param level: str, the level to log
    :param filename: str, the file to log to
    """
    import logging

    if logging.getLoggerClass() is not Logging:
        logging.setLoggerClass(Logging)
        logging.addLevelName(5, 'TRACE')
        logging.addLevelName(1, 'GARBAGE')

    level = levels.get(level, logging.ERROR)

    rootLogger = logging.getLogger()

    if filename and filemode=='a':
        import logging.handlers
        handler = logging.handlers.RotatingFileHandler(
            filename, filemode,
            maxBytes=50*1024*1024,   # 50 Mb
            backupCount=3,
            encoding='utf-8',
            delay=0
        )
    elif filename and filemode=='w':
        import logging.handlers
        handler = getattr(
            logging.handlers, 'WatchedFileHandler', logging.FileHandler)(
                filename, filemode, 'utf-8', delay=0
        )
    else:
        handler = logging.StreamHandler()

    handler.setLevel(level)

    formatter = logging.Formatter(
        DEFAULT_LOGGING_FORMAT % MAX_LOGGER_NAME_LENGTH,
        datefmt="%H:%M:%S"
    )

    handler.setFormatter(formatter)
    rootLogger.addHandler(handler)
    rootLogger.setLevel(level)

    twisted_logging = PythonLoggingObserver('twisted')
    twisted_logging.start()
    logging.getLogger("twisted").setLevel(level)

def tweak_logging_levels():
    """This function allows tweaking the logging levels for all or some loggers.
    This is mostly usefull for developing purposes hence the contents of the
    file are NOT like regular deluge config file's.

    To use is, create a file named "logging.conf" on your Deluge's config dir
    with contents like for example:
        deluge:warn
        deluge.core:debug
        deluge.plugin:error

    What the above mean is the logger "deluge" will be set to the WARN level,
    the "deluge.core" logger will be set to the DEBUG level and the
    "deluge.plugin" will be set to the ERROR level.

    Remember, one rule per line and this WILL override the setting passed from
    the command line.
    """
    from deluge import configmanager
    logging_config_file = os.path.join(configmanager.get_config_dir(),
                                       'logging.conf')
    if not os.path.isfile(logging_config_file):
        return
    log = logging.getLogger(__name__)
    log.warn("logging.conf found! tweaking logging levels from %s",
             logging_config_file)
    for line in open(logging_config_file, 'r').readlines():
        if line.strip().startswith("#"):
            continue
        name, level = line.strip().split(':')
        if level not in levels:
            continue

        log.warn("Setting logger \"%s\" to logging level \"%s\"", name, level)
        setLoggerLevel(level, name)


def setLoggerLevel(level, logger_name=None):
    """
    Sets the logger level.

    :param level: str, a string representing the desired level
    :param logger_name: str, a string representing desired logger name for which
                        the level should change. The default is "None" will will
                        tweak the root logger level.

    """
    logging.getLogger(logger_name).setLevel(levels.get(level, "error"))


def getPluginLogger(logger_name):
    import warnings
    stack = inspect.stack()
    stack.pop(0)                # The logging call from this module
    module_stack = stack.pop(0) # The module that called the log function
    caller_module = inspect.getmodule(module_stack[0])
    # In some weird cases caller_module might be None, try to continue
    caller_module_name = getattr(caller_module, '__name__', '')
    warnings.warn_explicit(DEPRECATION_WARNING, DeprecationWarning,
                           module_stack[1], module_stack[2],
                            caller_module_name)

    if 'deluge.plugins.' in logger_name:
        return logging.getLogger(logger_name)
    return logging.getLogger("deluge.plugin.%s" % logger_name)


DEPRECATION_WARNING = """You seem to be using old style logging on your code, ie:
    from deluge.log import LOG as log

or:
    from deluge.log import getPluginLogger

This has been deprecated in favour of an enhanced logging system and both "LOG"
and "getPluginLogger" will be removed on the next major version release of Deluge,
meaning, code will break, specially plugins.
If you're seeing this message and you're not the developer of the plugin which
triggered this warning, please report to it's author.
If you're the developer, please stop using the above code and instead use:

   import logging
   log = logging.getLogger(__name__)


The above will result in, regarding the "Label" plugin for example a log message similar to:
   15:33:54 [deluge.plugins.label.core:78  ][INFO    ] *** Start Label plugin ***

Triggering code:"""

class __BackwardsCompatibleLOG(object):
    def __getattribute__(self, name):
        import warnings
        logger_name = 'deluge'
        stack = inspect.stack()
        stack.pop(0)                # The logging call from this module
        module_stack = stack.pop(0) # The module that called the log function
        caller_module = inspect.getmodule(module_stack[0])
        # In some weird cases caller_module might be None, try to continue
        caller_module_name = getattr(caller_module, '__name__', '')
        warnings.warn_explicit(DEPRECATION_WARNING, DeprecationWarning,
                               module_stack[1], module_stack[2],
                               caller_module_name)
        if caller_module:
            for member in stack:
                module = inspect.getmodule(member[0])
                if not module:
                    continue
                if module.__name__ in ('deluge.plugins.pluginbase',
                                       'deluge.plugins.init'):
                    logger_name += '.plugin.%s' % caller_module_name
                    # Monkey Patch The Plugin Module
                    caller_module.log = logging.getLogger(logger_name)
                    break
        else:
            logging.getLogger(logger_name).warning(
                "Unable to monkey-patch the calling module's `log` attribute! "
                "You should really update and rebuild your plugins..."
            )
        return getattr(logging.getLogger(logger_name), name)

LOG = __BackwardsCompatibleLOG()
