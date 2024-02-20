#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import datetime
import time

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from deluge.common import create_localclient_account
from deluge.config import Config
from deluge.conftest import BaseTestCase
from deluge.tests.common import get_test_data_file
from deluge.ui.client import Client


def generate_x509_cert(common_name, san_list=None):
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    builder = (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name(
                [
                    x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                ]
            )
        )
        .not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=90))
        .serial_number(x509.random_serial_number())
        .public_key(private_key.public_key())
    )

    if san_list:
        san_objects = [
            x509.DNSName(str(san).strip()) for san in san_list if str(san).strip()
        ]
        builder = builder.add_extension(
            x509.SubjectAlternativeName(san_objects), critical=False
        )

    return private_key, builder


def x509_ca():
    common_name = 'Test CA'
    private_key, builder = generate_x509_cert(
        common_name=common_name,
    )
    builder = builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=1),
        critical=True,
    ).issuer_name(
        x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ]
        )
    )
    certificate = builder.sign(
        private_key=private_key,
        algorithm=hashes.SHA256(),
        backend=default_backend(),
    )
    return certificate, private_key


def x509_peer_certificate_pem(torrent_name, ca_cert, ca_key):
    private_key, builder = generate_x509_cert(
        common_name='doesnt_matter',
        san_list=[torrent_name],
    )
    builder = builder.issuer_name(ca_cert.issuer)
    certificate = builder.sign(
        private_key=ca_key, algorithm=hashes.SHA256(), backend=default_backend()
    )

    certificate_pem = certificate.public_bytes(
        encoding=serialization.Encoding.PEM
    ).decode()
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    return certificate_pem, private_key_pem


DH_PARAMS_PEM = """
-----BEGIN DH PARAMETERS-----
MIIBCAKCAQEA+oeNEEXOCzrdmDwkKb31I+WaGIeRlx9jvF4sold3Mrw8tQ8rqyfc
GNfjEUhqSnyROQ9Wf8BvQJ94Fcw3oV9Os3APZtHOwTag3PzSe2ImCHTWL+LbQD/m
bl2zDJ2xD6j1ZmyGes8DZC8RyBEMSS/aoWFKWKzlba5WXTzC8n/2MBReoOm2eMhF
wUG21UW/MQQ+i1sHrC0d0zPdvnqXAa7tnO70j/kLhxv8446fsbXJo4G/iIAR1RSD
UbMIXHrloW/G5BviauWNxIwvfTYTlzfzwhhCDieLI/GwuAF388BKG4KQ181qrTFO
iTniEzsEklfNUEZ59lwiDmJF1qmmH017PwIBAg==
-----END DH PARAMETERS-----
"""

CA_CERT, CA_KEY = x509_ca()


async def _create_daemon_and_client(daemon_factory, config_dir):
    certificate_location = config_dir / 'ssl_torrents_certs'
    certificate_location.mkdir()

    # Write default SSL certificates
    crt_pem, key_pem = x509_peer_certificate_pem(
        torrent_name='*',
        ca_cert=CA_CERT,
        ca_key=CA_KEY,
    )
    with open(certificate_location / 'default.crt.pem', 'w') as file:
        file.write(crt_pem)
    with open(certificate_location / 'default.key.pem', 'w') as file:
        file.write(key_pem)
    with open(certificate_location / 'default.dh.pem', 'w') as file:
        file.write(DH_PARAMS_PEM)

    # Open SSL port and set the certificate location in Deluge configuration
    config = Config(
        'core.conf',
        config_dir=config_dir,
    )
    config.set_item('ssl_torrents', True)
    config.save()

    # Pre-create the authentication credentials
    username, password = create_localclient_account(auth_file=config_dir / 'auth')

    # Run the daemon and connect a client to it
    daemon = await daemon_factory(58900, config_dir=config_dir)
    client = Client()
    await client.connect(port=daemon.listen_port, username=username, password=password)

    return client


class TestSslTorrents(BaseTestCase):
    async def test_ssl_torrents(self, daemon_factory, tmp_path_factory):
        seeder = await _create_daemon_and_client(
            daemon_factory=daemon_factory,
            config_dir=tmp_path_factory.mktemp('seeder'),
        )
        leecher_config_dir = tmp_path_factory.mktemp('leecher')
        leecher = await _create_daemon_and_client(
            daemon_factory=daemon_factory, config_dir=leecher_config_dir
        )
        destination_dir = tmp_path_factory.mktemp('destination')

        # Create two SSL torrents and add them to the seeder and the leecher
        torrent_ids = {}
        for test_file in ('deluge.png', 'seo.svg'):
            filename, filedump = await seeder.core.create_torrent(
                path=get_test_data_file(test_file),
                tracker='localhost',
                piece_length=2**14,
                private=True,
                add_to_session=True,
                ca_cert=CA_CERT.public_bytes(encoding=serialization.Encoding.PEM),
                target=str(destination_dir / f'{test_file}.torrent'),
            )

            torrent_id = await leecher.core.add_torrent_file(
                filename=filename,
                filedump=filedump,
                options={'download_location': str(destination_dir)},
            )

            torrent_ids[test_file] = torrent_id

        # Add an explicit certificate for one of the two torrents.
        # The second torrent will use the default certificate for transfers.
        torrent_name = 'deluge.png'
        for client in seeder, leecher:
            crt_pem, key_pem = x509_peer_certificate_pem(
                torrent_name=torrent_name,
                ca_cert=CA_CERT,
                ca_key=CA_KEY,
            )
            await client.core.set_ssl_torrent_cert(
                torrent_ids[torrent_name], crt_pem, key_pem, DH_PARAMS_PEM
            )

        # Connect the two peers directly, without tracker
        seeder_port = await seeder.core.get_ssl_listen_port()
        if seeder_port < 0:
            seeder_conf = await seeder.core.get_config()
            seeder_port = seeder_conf['listen_random_port'] + 1
        for torrent_id in torrent_ids.values():
            await leecher.core.connect_peer(torrent_id, '127.0.0.1', seeder_port)

        # Wait for transfers to be executed
        max_wait_seconds = 10
        all_finished = False
        while max_wait_seconds > 0:
            all_finished = True
            for torrent_id in torrent_ids.values():
                status = await leecher.core.get_torrent_status(
                    torrent_id=torrent_id, keys=[]
                )
                all_finished = all_finished and status['is_finished']

            if all_finished:
                break

            time.sleep(1)
            max_wait_seconds -= 1
        assert all_finished

        # Ensure that certificates are removed on torrent removal
        certificate_location = leecher_config_dir / 'ssl_torrents_certs'
        torrent_id = torrent_ids[torrent_name]
        ssl_files = (
            certificate_location / f'{torrent_id}.crt.pem',
            certificate_location / f'{torrent_id}.key.pem',
            certificate_location / f'{torrent_id}.dh.pem',
        )
        for file in ssl_files:
            assert file.is_file()
        await leecher.core.remove_torrent(torrent_id, remove_data=False)
        for file in ssl_files:
            assert not file.is_file()
