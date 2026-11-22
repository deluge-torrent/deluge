#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
import stat
import sys

from deluge import crypto_utils


def test_generate_ssl_keys(config_dir):
    ssl_dir = config_dir / 'ssl'
    ssl_dir.mkdir(parents=True)
    pkey = ssl_dir / 'daemon.pkey'
    pkey.write_text('old')
    os.chmod(pkey, 0o644)

    crypto_utils.check_ssl_keys()

    cert = ssl_dir / 'daemon.cert'
    assert crypto_utils.get_context_factory(str(cert), str(pkey))
    if sys.platform != 'win32':
        for path in (cert, pkey):
            assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
