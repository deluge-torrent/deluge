import os
import sys
import tempfile
import time
from subprocess import PIPE, Popen

from twisted.internet.error import CannotListenError

import deluge.common
import deluge.configmanager
import deluge.core.preferencesmanager
import deluge.log

deluge.log.setup_logger("none")


def disable_new_release_check():
    deluge.core.preferencesmanager.DEFAULT_PREFS["new_release_check"] = False


def set_tmp_config_dir():
    config_directory = tempfile.mkdtemp()
    deluge.configmanager.set_config_dir(config_directory)
    return config_directory


def rpath(*args):
    return os.path.join(os.path.dirname(__file__), *args)

# Initialize gettext
deluge.common.setup_translations()


def start_core(listen_port=58846):
    cwd = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    daemon_script = """
import sys
import deluge.main

sys.argv.extend(['-d', '-c', '%s', '-L', 'info', '-p', '%d'])

deluge.main.start_daemon()
"""
    config_directory = set_tmp_config_dir()
    fp = tempfile.TemporaryFile()
    fp.write(daemon_script % (config_directory, listen_port))
    fp.seek(0)

    core = Popen([sys.executable], cwd=cwd, stdin=fp, stdout=PIPE, stderr=PIPE)
    while True:
        line = core.stderr.readline()
        if "starting on %d" % listen_port in line:
            time.sleep(0.3)  # Slight pause just incase
            break
        elif "Couldn't listen on localhost:%d" % listen_port in line:
            raise CannotListenError("localhost", listen_port, "Could not start deluge test client: %s" % line)
        elif 'Traceback' in line:
            raise SystemExit(
                "Failed to start core daemon. Do \"\"\" %s \"\"\" to see what's "
                "happening" %
                "python -c \"import sys; import tempfile; import deluge.main; "
                "import deluge.configmanager; config_directory = tempfile.mkdtemp(); "
                "deluge.configmanager.set_config_dir(config_directory); "
                "sys.argv.extend(['-d', '-c', config_directory, '-L', 'info']); "
                "deluge.main.start_daemon()\""
            )
    return core
