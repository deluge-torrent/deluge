# -*- coding: utf-8 -*-
#
# Copyright (C) Calum Lind 2017 <calumlind+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os
import uuid
from socket import gaierror, gethostbyname

from twisted.internet import defer

from deluge.common import get_localhost_auth
from deluge.config import Config
from deluge.configmanager import get_config_dir
from deluge.ui.client import Client, client

log = logging.getLogger(__name__)

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 58846
LOCALHOST = ('127.0.0.1', 'localhost')


def default_hostlist():
    """Create a new hosts key for hostlist with a localhost entry"""
    host_id = uuid.uuid4().hex
    username, password = get_localhost_auth()
    return {'hosts': [(host_id, DEFAULT_HOST, DEFAULT_PORT, username, password)]}


def validate_host_info(hostname, port):
    """Checks that hostname and port are valid.

    Args:
        hostname (str): The IP or hostname of the deluge daemon.
        port (int): The port of the deluge daemon.

    Raises:
        ValueError: Host details are not valid with reason.
    """

    try:
        gethostbyname(hostname)
    except gaierror as ex:
        raise ValueError('Host %s: %s', hostname, ex.args[1])

    if not isinstance(port, int):
        raise ValueError('Invalid port. Must be an integer')


def migrate_hostlist(old_filename, new_filename):
    """Check for old hostlist filename and save details to new filename"""
    old_hostlist = get_config_dir(old_filename)
    if os.path.isfile(old_hostlist):
        config_v2 = Config(old_filename, config_dir=get_config_dir())
        config_v2.save(get_config_dir(new_filename))
        del config_v2

        try:
            os.rename(old_hostlist, old_hostlist + '.old')
        except OSError as ex:
            log.exception(ex)

        try:
            os.remove(old_hostlist + '.bak')
        except OSError:
            pass


def migrate_config_2_to_3(config):
    """Mirgrates old hostlist config files to new file version"""
    localclient_username, localclient_password = get_localhost_auth()
    if not localclient_username:
        # Nothing to do here, there's no auth file
        return
    for idx, (__, host, __, username, __) in enumerate(config['hosts'][:]):
        if host in LOCALHOST and not username:
            config['hosts'][idx][3] = localclient_username
            config['hosts'][idx][4] = localclient_password
    return config


class HostList(object):
    """This class contains methods for adding, removing and looking up hosts in hostlist.conf."""

    def __init__(self):
        migrate_hostlist('hostlist.conf.1.2', 'hostlist.conf')
        self.config = Config(
            'hostlist.conf',
            default_hostlist(),
            config_dir=get_config_dir(),
            file_version=3,
        )
        self.config.run_converter((1, 2), 3, migrate_config_2_to_3)
        self.config.save()

    def check_info_exists(self, hostname, port, username, skip_host_id=None):
        """Check for existing host entries with the same details.

        Args:
            hostname (str): The IP or hostname of the deluge daemon.
            port (int): The port of the deluge daemon.
            username (str): The username to login to the daemon with.
            skip_host_id (str): A host_id to skip to check if other hosts match details.

        Raises:
            ValueError: Host details already exist.

        """
        for host_entry in self.config['hosts']:
            if (hostname, port, username) == (
                host_entry[1],
                host_entry[2],
                host_entry[3],
            ):
                if skip_host_id is not None and skip_host_id == host_entry[0]:
                    continue
                raise ValueError('Host details already in hostlist')

    def add_host(self, hostname, port, username, password):
        """Add a new host to hostlist.

        Args:
            hostname (str): The IP or hostname of the deluge daemon.
            port (int): The port of the deluge daemon.
            username (str): The username to login to the daemon with.
            password (str): The password to login to the daemon with.

        Returns:
            str: The new host id.
        """
        if (
            not password and not username or username == 'localclient'
        ) and hostname in LOCALHOST:
            username, password = get_localhost_auth()

        validate_host_info(hostname, port)
        self.check_info_exists(hostname, port, username)
        host_id = uuid.uuid4().hex
        self.config['hosts'].append((host_id, hostname, port, username, password))
        self.config.save()
        return host_id

    def get_host_info(self, host_id):
        """Get the host details for host_id.

        Args:
            host_id (str): The host id to get info on.

        Returns:
            list: A list of (host_id, hostname, port, username).

        """
        for host_entry in self.config['hosts']:
            if host_entry[0] == host_id:
                return host_entry[0:4]
        else:
            return []

    def get_hosts_info(self):
        """Get information of all the hosts in the hostlist.

        Returns:
            list of lists: Host information in the format [(host_id, hostname, port, username)].

        """
        return [host_entry[0:4] for host_entry in self.config['hosts']]

    def get_host_status(self, host_id):
        """Gets the current status (online/offline) of the host

        Args:
            host_id (str): The host id to check status of.

        Returns:
            tuple: A tuple of strings (host_id, status, version).

        """
        status_offline = (host_id, 'Offline', '')

        def on_connect(result, c, host_id):
            """Successfully connected to a daemon"""

            def on_info(info, c):
                c.disconnect()
                return host_id, 'Online', info

            def on_info_fail(reason, c):
                c.disconnect()
                return status_offline

            return c.daemon.info().addCallback(on_info, c).addErrback(on_info_fail, c)

        def on_connect_failed(reason, host_id):
            """Connection to daemon failed"""
            log.debug('Host status failed for %s: %s', host_id, reason)
            return status_offline

        try:
            host_id, host, port, user = self.get_host_info(host_id)
        except ValueError:
            log.warning('Problem getting host_id info from hostlist')
            return defer.succeed(status_offline)

        try:
            ip = gethostbyname(host)
        except gaierror as ex:
            log.error('Error resolving host %s to ip: %s', host, ex.args[1])
            return defer.succeed(status_offline)

        host_conn_info = (
            ip,
            port,
            'localclient' if not user and host in LOCALHOST else user,
        )
        if client.connected() and host_conn_info == client.connection_info():
            # Currently connected to host_id daemon.
            def on_info(info, host_id):
                log.debug('Client connected, query info: %s', info)
                return host_id, 'Connected', info

            return client.daemon.info().addCallback(on_info, host_id)
        else:
            # Attempt to connect to daemon with host_id details.
            c = Client()
            d = c.connect(host, port, skip_authentication=True)
            d.addCallback(on_connect, c, host_id)
            d.addErrback(on_connect_failed, host_id)
            return d

    def update_host(self, host_id, hostname, port, username, password):
        """Update the supplied host id with new connection details.

        Args:
            host_id (str): The host id to update.
            hostname (str): The new IP or hostname of the deluge daemon.
            port (int): The new port of the deluge daemon.
            username (str): The new username to login to the daemon with.
            password (str): The new password to login to the daemon with.

        """
        validate_host_info(hostname, port)
        self.check_info_exists(hostname, port, username, skip_host_id=host_id)

        if (
            not password and not username or username == 'localclient'
        ) and hostname in LOCALHOST:
            username, password = get_localhost_auth()

        for idx, host_entry in enumerate(self.config['hosts']):
            if host_id == host_entry[0]:
                self.config['hosts'][idx] = host_id, hostname, port, username, password
                self.config.save()
                return True
        return False

    def remove_host(self, host_id):
        """Removes the host entry from hostlist config.

        Args:
            host_id (str): The host id to remove.

        Returns:
            bool: True is successfully removed, False otherwise.

        """
        for host_entry in self.config['hosts']:
            if host_id == host_entry[0]:
                self.config['hosts'].remove(host_entry)
                self.config.save()
                return True
        else:
            return False

    def add_default_host(self):
        self.add_host(DEFAULT_HOST, DEFAULT_PORT, *get_localhost_auth())

    def connect_host(self, host_id):
        """Connect to host daemon"""
        for host_entry in self.config['hosts']:
            if host_entry[0] == host_id:
                __, host, port, username, password = host_entry
                return client.connect(host, port, username, password)

        return defer.fail(Exception('Bad host id'))
