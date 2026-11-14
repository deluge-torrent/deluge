"""Coverage for session settings removed or renamed by newer libtorrent builds."""

from types import SimpleNamespace
from unittest import mock

import pytest

from deluge.core.core import REMOVED_SESSION_SETTINGS, Core


def make_core(settings):
    session = mock.Mock()
    session.get_settings.return_value = settings
    return SimpleNamespace(session=session)


def test_legacy_settings_are_ignored_only_when_unavailable():
    core = make_core({'connections_limit': 200, 'peer_dscp': 0})
    changes = {name: 123 for name in REMOVED_SESSION_SETTINGS}
    changes.update({'connections_limit': 300, 'peer_tos': 16})
    with mock.patch('deluge.core.core.log.warning') as warning:
        Core.apply_session_settings(core, changes)

    core.session.apply_settings.assert_called_once_with(
        {'connections_limit': 300, 'peer_dscp': 16}
    )
    assert {
        call.args[-1] for call in warning.call_args_list
    } == REMOVED_SESSION_SETTINGS


def test_legacy_settings_are_retained_when_supported():
    core = make_core({'cache_size': 512, 'peer_tos': 0, 'force_proxy': False})
    changes = {'cache_size': 256, 'peer_tos': 8, 'force_proxy': True}
    with mock.patch('deluge.core.core.LT_VERSION', '1.2.19.0'):
        Core.apply_session_settings(core, changes)
    core.session.apply_settings.assert_called_once_with(changes)


def test_unsupported_force_proxy_never_silently_disappears():
    core = make_core({'proxy_type': 0, 'force_proxy': False})
    with mock.patch('deluge.core.core.LT_VERSION', '2.1.0.0'):
        with pytest.raises(ValueError, match='force_proxy'):
            Core.apply_session_settings(core, {'proxy_type': 2, 'force_proxy': True})
    core.session.apply_settings.assert_not_called()
    core.session.pause.assert_called_once_with()


def test_force_proxy_configuration_is_rejected_before_session_start():
    saved_config = {'proxy': {'force_proxy': True}}
    with mock.patch('deluge.core.core.LT_VERSION', '2.1.0.0'):
        with mock.patch('deluge.core.core.ConfigManager', return_value=saved_config):
            with mock.patch('deluge.core.core.lt.session') as session:
                with pytest.raises(ValueError, match='force_proxy'):
                    Core()
                session.assert_not_called()


def test_disabled_removed_force_proxy_can_be_ignored():
    core = make_core({'proxy_type': 0, 'force_proxy': False})
    with mock.patch('deluge.core.core.LT_VERSION', '2.1.0.0'):
        Core.apply_session_settings(core, {'proxy_type': 0, 'force_proxy': False})
    core.session.apply_settings.assert_called_once_with({'proxy_type': 0})


def test_unrecognised_session_setting_is_not_ignored():
    core = make_core({'connections_limit': 200})
    with pytest.raises(KeyError, match='unknown_setting'):
        Core.apply_session_settings(core, {'unknown_setting': 5})
    core.session.apply_settings.assert_not_called()
