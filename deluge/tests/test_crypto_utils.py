"""Tests for daemon TLS certificate generation with modern cryptography."""

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509.oid import NameOID

from deluge import crypto_utils


def test_daemon_certificate_and_context_factory(tmp_path, monkeypatch):
    ssl_dir = tmp_path / 'ssl'
    monkeypatch.setattr(
        crypto_utils.deluge.configmanager,
        'get_config_dir',
        lambda name: str(ssl_dir),
    )

    crypto_utils.check_ssl_keys()
    key_path = ssl_dir / 'daemon.pkey'
    cert_path = ssl_dir / 'daemon.cert'

    key_data = key_path.read_bytes()
    cert_data = cert_path.read_bytes()
    key = serialization.load_pem_private_key(key_data, password=None)
    cert = x509.load_pem_x509_certificate(cert_data)

    assert cert.subject == cert.issuer
    assert cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == (
        'Deluge Daemon'
    )
    assert cert.public_key().public_numbers() == key.public_key().public_numbers()
    cert.public_key().verify(
        cert.signature,
        cert.tbs_certificate_bytes,
        padding.PKCS1v15(),
        cert.signature_hash_algorithm,
    )

    context_factory = crypto_utils.get_context_factory(str(cert_path), str(key_path))
    assert context_factory.getContext() is not None

    # Existing certificates should be preserved across daemon restarts.
    crypto_utils.check_ssl_keys()
    assert key_path.read_bytes() == key_data
    assert cert_path.read_bytes() == cert_data
