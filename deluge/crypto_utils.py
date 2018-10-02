# -*- coding: utf-8 -*-
#
# Copyright (C) 2007,2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import division, print_function, unicode_literals

from OpenSSL.crypto import FILETYPE_PEM
from twisted.internet.ssl import (
    AcceptableCiphers,
    Certificate,
    CertificateOptions,
    KeyPair,
    TLSVersion,
)

# A TLS ciphers list.
# Sources for more information on TLS ciphers:
# - https://wiki.mozilla.org/Security/Server_Side_TLS
# - https://www.ssllabs.com/projects/best-practices/index.html
# - https://hynek.me/articles/hardening-your-web-servers-ssl-ciphers/
#
# This list was inspired by the `urllib3` library
# - https://github.com/urllib3/urllib3/blob/master/urllib3/util/ssl_.py#L79
#
# The general intent is:
# - prefer cipher suites that offer perfect forward secrecy (ECDHE),
# - prefer AES-GCM over ChaCha20 because hardware-accelerated AES is common,
# - disable NULL authentication, MD5 MACs and DSS for security reasons.
TLS_CIPHERS = ':'.join(
    [
        'ECDH+AESGCM',
        'ECDH+CHACHA20',
        'AES256-GCM-SHA384',
        'AES128-GCM-SHA256',
        '!DSS' '!aNULL',
        '!eNULL',
        '!MD5',
    ]
)

# This value tells OpenSSL to disable all SSL/TLS renegotiation.
SSL_OP_NO_RENEGOTIATION = 0x40000000


def get_context_factory(cert_path, pkey_path):
    """OpenSSL context factory.

    Generates an OpenSSL context factory using Twisted's CertificateOptions class.
    This will keep a server cipher order.

    Args:
        cert_path (string): The path to the certificate file
        pkey_path (string): The path to the private key file

    Returns:
        twisted.internet.ssl.CertificateOptions: An OpenSSL context factory
    """

    with open(cert_path) as cert:
        certificate = Certificate.loadPEM(cert.read()).original
    with open(pkey_path) as pkey:
        private_key = KeyPair.load(pkey.read(), FILETYPE_PEM).original
    ciphers = AcceptableCiphers.fromOpenSSLCipherString(TLS_CIPHERS)
    cert_options = CertificateOptions(
        privateKey=private_key,
        certificate=certificate,
        raiseMinimumTo=TLSVersion.TLSv1_2,
        acceptableCiphers=ciphers,
    )
    ctx = cert_options.getContext()
    ctx.use_certificate_chain_file(cert_path)
    ctx.set_options(SSL_OP_NO_RENEGOTIATION)

    return cert_options
