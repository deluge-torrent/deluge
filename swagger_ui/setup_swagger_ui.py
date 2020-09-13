#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2020 Bendik Rønning Opstad <bro.devel@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from __future__ import print_function, unicode_literals

import argparse
import ast
import json
import os
import subprocess
from subprocess import call, check_output

DEFAULT_VERSION = '3.33.0'


class SwaggerSetupError(Exception):
    pass


script_dir = os.path.dirname(os.path.abspath(__file__))
swagger_ui_dist = os.path.join(script_dir, 'node_modules', 'swagger-ui-dist')


def get_available_versions():
    versions = check_output(['npm', 'view', 'swagger-ui-dist', 'versions']).strip().decode()
    versions = ast.literal_eval(versions)
    return versions


def download_swagger_ui(version):
    """
    Download swagger-ui-dist to local directory
    """
    try:
        versions = check_output(['npm', 'install',
                                 '--prefix', script_dir, 'swagger-ui-dist@{}'.format(version)]).strip().decode()
    except subprocess.CalledProcessError as exc:
        out = exc.output.decode()
        print("npm install failed with status '{}': {}".format(exc.returncode, out))
        return
    return versions


def install_swagger_ui():
    """
    Install the downloaded swagger-ui files into Deluge UI directory
    """
    import shutil

    deluge_root_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
    deluge_swagger_dest_dir = os.path.join(deluge_root_dir, 'deluge/ui/web/js/swagger-ui')
    if os.path.isdir(deluge_swagger_dest_dir):
        print("Deleting already existing directory '{}'".format(deluge_swagger_dest_dir))
        shutil.rmtree(deluge_swagger_dest_dir)

    print('Installing Swagger UI into {}'.format(deluge_swagger_dest_dir))
    shutil.copytree(swagger_ui_dist, deluge_swagger_dest_dir)

    print('Copy index.html into {}'.format(swagger_ui_dist))
    index_file = os.path.join(script_dir, 'index.html')
    shutil.copy(index_file, deluge_swagger_dest_dir)


def get_downloaded_version():
    if not os.path.isdir(swagger_ui_dist):
        raise SwaggerSetupError("Package swagger-ui-dist not installed")

    with open(os.path.join(swagger_ui_dist, 'package.json'), 'r') as f:
        package = json.loads(f.read())
        return package['version']


def parse_args():
    parser = argparse.ArgumentParser(description='List the content of a folder')
    parser.add_argument('-l', '--list-versions', action='store_true', help='List available versions')
    parser.add_argument('--version', default=DEFAULT_VERSION, help='Version to download. Default: %(default)s')
    parser.add_argument('--download', action='store_true', help='Download swagger-ui-dist package')
    parser.add_argument('--install', action='store_true', help='Install swagger-ui into Deluge UI directory')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    if args.list_versions:
        versions = get_available_versions()
        print("Available versions for package swagger-ui-dist:", versions)
    elif args.download:
        version = get_downloaded_version()
        if args.version == version:
            print("The requested version '{}' is already installed".format(args.version))
        else:
            print('Downloading swagger-ui-dist version "{}"'.format(args.version))
            download_swagger_ui(args.version)
    elif args.install:
        print('Installing swagger-ui-dist version "{}"'.format(args.version))
        install_swagger_ui()
    else:
        try:
            version = get_downloaded_version()
        except SwaggerSetupError:
            version = None
        # If not installed, or version mismatch, download swagger-ui-dist package
        if args.version != version:
            download_swagger_ui(args.version)
        install_swagger_ui()
