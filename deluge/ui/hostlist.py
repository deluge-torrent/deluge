# -*- coding: utf-8 -*-
#
# Copyright (C) Calum Lind 2017 <calumlind+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""
The UI hostlist module contains methods useful for adding, removing and lookingup host in hostlist.conf.
"""
from __future__ import unicode_literals

import logging
import os
import time
from hashlib import sha1
from socket import gaierror, gethostbyname

from deluge.config import Config
from deluge.configmanager import get_config_dir

log = logging.getLogger(__name__)

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 58846
LOCALHOST = ('127.0.0.1', 'localhost')


def default_hostlist():
    """Create a new hosts for hostlist with a localhost entry"""
    host_id = sha1(str(time.time()).encode('utf8')).hexdigest()
    username, password = get_localhost_auth()
    return {'hosts': [(host_id, DEFAULT_HOST, DEFAULT_PORT, username, password)]}


def get_localhost_auth():
        """Grabs the localclient auth line from the 'auth' file and creates a localhost uri.

        Returns:
            tuple: With the username and password to login as.

        """
        auth_file = get_config_dir('auth')
        if not os.path.exists(auth_file):
            from deluge.common import create_localclient_account
            create_localclient_account()

        with open(auth_file) as auth:
            for line in auth:
                line = line.strip()
                if line.startswith('#') or not line:
                    # This is a comment or blank line
                    continue

                lsplit = line.split(':')

                if len(lsplit) == 2:
                    username, password = lsplit
                elif len(lsplit) == 3:
                    username, password, level = lsplit
                else:
                    log.error('Your auth file is malformed: Incorrect number of fields!')
                    continue

                if username == 'localclient':
                    return (username, password)


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

    try:
        int(port)
    except ValueError:
        raise ValueError('Invalid port. Must be an integer')


def _migrate_config_1_to_2(config):
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
    def __init__(self):
        self.config = Config('hostlist.conf', default_hostlist(), config_dir=get_config_dir(), file_version=2)
        self.config.run_converter((0, 1), 2, _migrate_config_1_to_2)
        self.config.save()

    def check_info_exists(self, hostname, port, username, skip_host_id=None):
        """Check for exising host entries with the same details.

        Args:
            hostname (str): The IP or hostname of the deluge daemon.
            port (int): The port of the deluge daemon.
            username (str): The username to login to the daemon with.
            skip_host_id (str): A host_id to skip to check if other hosts match details.

        Raises:
            ValueError: Host details already exist.

        """
        for host_entry in self.config['hosts']:
            if (hostname, port, username) == (host_entry[1], host_entry[2], host_entry[3]):
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
        if (not password and not username or username == 'localclient') and hostname in LOCALHOST:
                username, password = get_localhost_auth()

        validate_host_info(hostname, port)
        self.check_info_exists(hostname, port, username)
        host_id = sha1(str(time.time())).hexdigest()
        self.config['hosts'].append((host_id, hostname, port, username, password))
        self.config.save()
        return host_id

    def get_host_info(self, host_id):
        """Get the host details for host_id.

        Includes password details!

        """
        for host_entry in self.config['hosts']:
            if host_entry[0] == host_id:
                return host_entry
        else:
            return []

    def get_hosts_info(self):
        """Get all the hosts in the hostlist

        Excluding password details.
        """
        return [host[0:4 + 1] for host in self.config['hosts']]

    def get_hosts_info2(self):
        """Get all the hosts in the hostlist

        Excluding password details.
        """
        return [host for host in self.config['hosts']]

    def update_host(self, host_id, hostname, port, username, password):
        """Update the host with new details.

        Args:
            host_id (str): The host id to update.
            hostname (str): The new IP or hostname of the deluge daemon.
            port (int): The new port of the deluge daemon.
            username (str): The new username to login to the daemon with.
            password (str): The new password to login to the daemon with.

        """
        validate_host_info(hostname, port)
        self.check_info_exists(hostname, port, username, skip_host_id=host_id)

        if (not password and not username or username == 'localclient') and hostname in LOCALHOST:
            username, password = get_localhost_auth()

        for host_entry in self.config['hosts']:
            if host_id == host_entry[0]:
                host_entry = host_id, hostname, port, username, password
                return True
        return False

    def remove_host(self, host_id):
        for host_entry in self.config['hosts']:
            if host_id == host_entry[0]:
                self.config['hosts'].remove(host_entry)
                self.config.save()
                return True
        else:
            return False

    def add_default_host(self):
        self.add_host(DEFAULT_HOST, DEFAULT_PORT, *get_localhost_auth())
