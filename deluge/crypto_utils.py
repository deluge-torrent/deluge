#
# Copyright (C) 2007,2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
import stat
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from OpenSSL.crypto import FILETYPE_PEM
from twisted.internet.ssl import (
    AcceptableCiphers,
    Certificate,
    CertificateOptions,
    KeyPair,
    TLSVersion,
)

import deluge.configmanager

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
        '!DSS!aNULL',
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


def check_ssl_keys():
    """
    Check for SSL cert/key and create them if necessary
    """
    ssl_dir = deluge.configmanager.get_config_dir('ssl')
    if not os.path.exists(ssl_dir):
        # The ssl folder doesn't exist so we need to create it
        os.makedirs(ssl_dir)
        generate_ssl_keys()
    else:
        for f in ('daemon.pkey', 'daemon.cert'):
            if not os.path.exists(os.path.join(ssl_dir, f)):
                generate_ssl_keys()
                break


def generate_ssl_keys():
    """
    This method generates a new SSL key/cert.
    """
    # Generate key pair
    pkey = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Generate certificate
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Deluge Daemon')])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(pkey.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365 * 3))  # Three Years
        .sign(pkey, hashes.SHA256())
    )

    ssl_dir = deluge.configmanager.get_config_dir('ssl')
    files = {
        'daemon.pkey': pkey.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        'daemon.cert': cert.public_bytes(serialization.Encoding.PEM),
    }
    for name, data in files.items():
        path = os.path.join(ssl_dir, name)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, 'wb') as _file:
            _file.write(data)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
