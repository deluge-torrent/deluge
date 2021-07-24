# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function, unicode_literals

import os
import sys
import tempfile
import traceback

from twisted.internet import defer, protocol, reactor
from twisted.internet.defer import Deferred
from twisted.internet.error import CannotListenError
from twisted.trial import unittest

import deluge.configmanager
import deluge.core.preferencesmanager
import deluge.log
from deluge.error import DelugeError

# This sets log level to critical, so use log.critical() to debug while running unit tests
deluge.log.setup_logger('none')


def disable_new_release_check():
    deluge.core.preferencesmanager.DEFAULT_PREFS['new_release_check'] = False


def set_tmp_config_dir():
    config_directory = tempfile.mkdtemp()
    deluge.configmanager.set_config_dir(config_directory)
    return config_directory


def setup_test_logger(level='info', prefix='deluge'):
    deluge.log.setup_logger(level, filename='%s.log' % prefix, twisted_observer=False)


def get_test_data_file(filename):
    return os.path.join(os.path.join(os.path.dirname(__file__), 'data'), filename)


def todo_test(caller):
    # If we are using the delugereporter we can set todo mark on the test
    # Without the delugereporter the todo would print a stack trace, so in
    # that case we rely only on skipTest
    if os.environ.get('DELUGE_REPORTER', None):
        getattr(caller, caller._testMethodName).__func__.todo = 'To be fixed'

    filename = os.path.basename(traceback.extract_stack(None, 2)[0][0])
    funcname = traceback.extract_stack(None, 2)[0][2]
    raise unittest.SkipTest('TODO: %s:%s' % (filename, funcname))


def add_watchdog(deferred, timeout=0.05, message=None):
    def callback(value):
        if not watchdog.called and not watchdog.cancelled:
            watchdog.cancel()
        if not deferred.called:
            if message:
                print(message)
            deferred.cancel()
        return value

    deferred.addBoth(callback)
    watchdog = reactor.callLater(timeout, defer.Deferred.addTimeout, deferred)
    return watchdog


class ReactorOverride(object):
    """Class used to patch reactor while running unit tests
    to avoid starting and stopping the twisted reactor
    """

    def __getattr__(self, attr):
        if attr == 'run':
            return self._run
        if attr == 'stop':
            return self._stop
        return getattr(reactor, attr)

    def _run(self):
        pass

    def _stop(self):
        pass

    def addReader(self, arg):  # NOQA: N802
        pass


class ProcessOutputHandler(protocol.ProcessProtocol):
    def __init__(
        self, script, callbacks, logfile=None, print_stdout=True, print_stderr=True
    ):
        """Executes a script and handle the process' output to stdout and stderr.

        Args:
            script (str): The script to execute.
            callbacks (list): Callbacks to trigger if the expected output if found.
            logfile (str, optional): Filename to wrote the process' output.
            print_stderr (bool): Print the process' stderr output to stdout.
            print_stdout (bool): Print the process' stdout output to stdout.

        """
        self.callbacks = callbacks
        self.script = script
        self.log_output = ''
        self.stderr_out = ''
        self.logfile = logfile
        self.print_stdout = print_stdout
        self.print_stderr = print_stderr
        self.quit_d = None
        self.killed = False
        self.watchdogs = []

    def connectionMade(self):  # NOQA: N802
        self.transport.write(self.script)
        self.transport.closeStdin()

    def outConnectionLost(self):  # NOQA: N802
        if not self.logfile:
            return
        with open(self.logfile, 'w') as f:
            f.write(self.log_output)

    def kill(self):
        """Kill the running process.

        Returns:
            Deferred: A deferred that is triggered when the process has quit.

        """
        if self.killed:
            return
        self.killed = True
        self._kill_watchdogs()
        self.quit_d = Deferred()
        self.transport.signalProcess('INT')
        return self.quit_d

    def _kill_watchdogs(self):
        """"Cancel all watchdogs"""
        for w in self.watchdogs:
            if not w.called and not w.cancelled:
                w.cancel()

    def processEnded(self, status):  # NOQA: N802
        self.transport.loseConnection()
        if self.quit_d is None:
            return
        if status.value.exitCode == 0:
            self.quit_d.callback(True)
        else:
            self.quit_d.errback(status)

    def check_callbacks(self, data, cb_type='stdout'):
        ret = False
        for c in self.callbacks:
            if cb_type not in c['types'] or c['deferred'].called:
                continue
            for trigger in c['triggers']:
                if trigger['expr'] in data:
                    ret = True
                    if 'cb' in trigger:
                        trigger['cb'](self, c['deferred'], data, self.log_output)
                    elif 'value' not in trigger:
                        raise Exception('Trigger must specify either "cb" or "value"')
                    else:
                        val = trigger['value'](self, data, self.log_output)
                        if trigger.get('type', 'callback') == 'errback':
                            c['deferred'].errback(val)
                        else:
                            c['deferred'].callback(val)
        return ret

    def outReceived(self, data):  # NOQA: N802
        """Process output from stdout"""
        data = data.decode('utf8')
        self.log_output += data
        if self.check_callbacks(data):
            pass
        elif '[ERROR' in data:
            if not self.print_stdout:
                return
            print(data, end=' ')

    def errReceived(self, data):  # NOQA: N802
        """Process output from stderr"""
        data = data.decode('utf8')
        self.log_output += data
        self.stderr_out += data
        self.check_callbacks(data, cb_type='stderr')
        if not self.print_stderr:
            return
        data = '\n%s' % data.strip()
        prefixed = data.replace('\n', '\nSTDERR: ')
        print('\n%s' % prefixed)


def start_core(
    listen_port=58846,
    logfile=None,
    timeout=10,
    timeout_msg=None,
    custom_script='',
    print_stdout=True,
    print_stderr=True,
    extra_callbacks=None,
):
    """Start the deluge core as a daemon.

    Args:
        listen_port (int, optional): The port the daemon listens for client connections.
        logfile (str, optional): Logfile name to write the output from the process.
        timeout (int): If none of the callbacks have been triggered before the imeout, the process is killed.
        timeout_msg (str): The message to print when the timeout expires.
        custom_script (str): Extra python code to insert into the daemon process script.
        print_stderr (bool): If the output from the process' stderr should be printed to stdout.
        print_stdout (bool): If the output from the process' stdout should be printed to stdout.
        extra_callbacks (list): A list of dictionaries specifying extra callbacks.

    Returns:
        tuple(Deferred, ProcessOutputHandler):

        The Deferred is fired when the core callback is triggered either after the default
        output triggers are matched (daemon successfully started, or failed to start),
        or upon timeout expiry. The ProcessOutputHandler is the handler for the deluged process.

    """
    config_directory = set_tmp_config_dir()
    daemon_script = """
import sys
import deluge.core.daemon_entry

from deluge.common import windows_check

if windows_check():
    sys.argv.extend(['-c', '%(dir)s', '-L', 'info', '-p', '%(port)d'])
else:
    sys.argv.extend(['-d', '-c', '%(dir)s', '-L', 'info', '-p', '%(port)d'])

try:
    daemon = deluge.core.daemon_entry.start_daemon(skip_start=True)
    %(script)s
    daemon.start()
except Exception:
    import traceback
    sys.stderr.write('Exception raised:\\n %%s' %% traceback.format_exc())
""" % {
        'dir': config_directory,
        'port': listen_port,
        'script': custom_script,
    }

    callbacks = []
    default_core_cb = {'deferred': Deferred(), 'types': 'stdout'}
    if timeout:
        default_core_cb['timeout'] = timeout

    # Specify the triggers for daemon log output
    default_core_cb['triggers'] = [
        {'expr': 'Finished loading ', 'value': lambda reader, data, data_all: reader},
        {
            'expr': 'Cannot start deluged, listen port in use.',
            'type': 'errback',
            'value': lambda reader, data, data_all: CannotListenError(
                'localhost',
                listen_port,
                'Could not start deluge test client!\n%s' % data,
            ),
        },
        {
            'expr': 'Traceback',
            'type': 'errback',
            'value': lambda reader, data, data_all: DelugeError(
                'Traceback found when starting daemon:\n%s' % data
            ),
        },
    ]

    callbacks.append(default_core_cb)
    if extra_callbacks:
        callbacks.extend(extra_callbacks)

    process_protocol = start_process(
        daemon_script, callbacks, logfile, print_stdout, print_stderr
    )
    return default_core_cb['deferred'], process_protocol


def start_process(
    script, callbacks, logfile=None, print_stdout=True, print_stderr=True
):
    """
    Starts an external python process which executes the given script.

    Args:
        script (str): The content of the script to execute.
        callbacks (list): list of dictionaries specifying callbacks.
        logfile (str, optional): Logfile name to write the output from the process.
        print_stderr (bool): If the output from the process' stderr should be printed to stdout.
        print_stdout (bool): If the output from the process' stdout should be printed to stdout.

    Returns:
        ProcessOutputHandler: The handler for the process's output.

    Each entry in the callbacks list is a dictionary with the following keys:
      * "deferred": The deferred to be called when matched.
      * "types": The output this callback should be matched against.
                 Possible values: ["stdout", "stderr"]
      * "timeout" (optional): A timeout in seconds for the deferred.
      * "triggers": A list of dictionaries, each specifying specifying a trigger:
        * "expr": A string to match against the log output.
        * "value": A function to produce the result to be passed to the callback.
        * "type" (optional): A string that specifies wether to trigger a regular callback or errback.

    """
    cwd = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    process_protocol = ProcessOutputHandler(
        script.encode('utf8'), callbacks, logfile, print_stdout, print_stderr
    )

    # Add timeouts to deferreds
    for c in callbacks:
        if 'timeout' in c:
            w = add_watchdog(
                c['deferred'], timeout=c['timeout'], message=c.get('timeout_msg', None)
            )
            process_protocol.watchdogs.append(w)

    reactor.spawnProcess(
        process_protocol, sys.executable, args=[sys.executable], path=cwd
    )
    return process_protocol
