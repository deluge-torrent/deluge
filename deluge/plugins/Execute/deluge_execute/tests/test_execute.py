#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import logging
import subprocess
import threading
import time

import pytest
import pytest_twisted
from twisted.internet import reactor, task

from deluge.common import windows_check
from deluge_execute import core as execute_core

pytestmark = pytest.mark.skipif(windows_check(), reason='uses a POSIX shell script')


class FakeTorrent:
    name = 'Some Torrent'

    def get_status(self, keys):
        return {'name': self.name, 'download_location': '/downloads'}


@pytest.fixture
def core(monkeypatch):
    components = {
        'TorrentManager': type('', (), {'torrents': {'abc123': FakeTorrent()}})
    }
    # Anything else, like RPCServer in CorePluginBase.__del__, gets a KeyError.
    monkeypatch.setattr(execute_core.component, 'get', components.__getitem__)
    plugin = execute_core.Core.__new__(execute_core.Core)
    plugin.config = {'commands': []}
    return plugin


def add_command(core, tmp_path, body, shebang='#!/bin/sh\n'):
    script = tmp_path / 'script.sh'
    script.write_text(shebang + body)
    script.chmod(0o755)
    core.config['commands'].append(('id', 'complete', str(script)))


async def wait_for(predicate, timeout=5):
    for _ in range(int(timeout / 0.05)):
        if predicate():
            return
        await task.deferLater(reactor, 0.05, lambda: None)
    pytest.fail('timed out')


def join_command_threads():
    for thread in threading.enumerate():
        if thread.name == 'Execute':
            thread.join(5)


@pytest_twisted.ensureDeferred
async def test_command_gets_torrent_args(core, tmp_path):
    out = tmp_path / 'args'
    add_command(
        core, tmp_path, f'printf "%s\\n" "$@" > {out}.tmp && mv {out}.tmp {out}\n'
    )

    core.execute_commands('abc123', 'complete')

    await wait_for(out.exists)
    assert out.read_text().splitlines() == ['abc123', 'Some Torrent', '/downloads']


@pytest_twisted.ensureDeferred
async def test_slow_spawn_does_not_block_caller(core, tmp_path, monkeypatch):
    # The spawn waits for the child to exec, which took seconds under heavy
    # disk IO, so the caller (the reactor) must not wait for it.
    started, release = threading.Event(), threading.Event()
    real_run = subprocess.run

    def slow_run(*args, **kwargs):
        started.set()
        release.wait(5)
        return real_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, 'run', slow_run)
    add_command(core, tmp_path, 'exit 0\n')

    try:
        start = time.monotonic()
        core.execute_commands('abc123', 'complete')
        assert time.monotonic() - start < 1
        await wait_for(started.is_set)
    finally:
        release.set()


def test_successful_command_logs_nothing(core, tmp_path, caplog):
    add_command(core, tmp_path, 'echo to-stdout; exit 0\n')

    with caplog.at_level(logging.WARNING):
        core.execute_commands('abc123', 'complete')
        join_command_threads()

    assert [r for r in caplog.records if r.name == execute_core.log.name] == []


@pytest_twisted.ensureDeferred
async def test_failed_command_logs_output(core, tmp_path, caplog):
    add_command(core, tmp_path, 'echo to-stdout; echo to-stderr >&2; exit 3\n')

    with caplog.at_level(logging.WARNING):
        core.execute_commands('abc123', 'complete')
        await wait_for(lambda: 'to-stderr' in caplog.text)

    assert 'failed with exit code 3' in caplog.text
    assert 'to-stdout' in caplog.text


@pytest_twisted.ensureDeferred
async def test_missing_script_logs_error(core, tmp_path, caplog):
    core.config['commands'].append(('id', 'complete', str(tmp_path / 'missing.sh')))

    with caplog.at_level(logging.WARNING):
        core.execute_commands('abc123', 'complete')
        await wait_for(lambda: 'not found or not executable' in caplog.text)


@pytest.mark.parametrize(
    'shebang, name',
    [('', 'Some Torrent'), ('#!/bin/sh\n', 'nul\x00name')],
    ids=['no-shebang', 'nul-in-name'],
)
def test_command_that_cannot_start_logs_warning(
    core, tmp_path, caplog, monkeypatch, shebang, name
):
    monkeypatch.setattr(FakeTorrent, 'name', name)
    add_command(core, tmp_path, 'exit 0\n', shebang=shebang)

    with caplog.at_level(logging.WARNING):
        core.execute_commands('abc123', 'complete')
        join_command_threads()

    assert 'failed to start' in caplog.text
