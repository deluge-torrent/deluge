# This file is adapted from Werkzeug (https://github.com/pallets/werkzeug)
# and is licensed under the BSD 3-Clause License:

# Copyright 2007 Pallets

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:

# 1.  Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.

# 2.  Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.

# 3.  Neither the name of the copyright holder nor the names of its
#     contributors may be used to endorse or promote products derived from
#     this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import annotations

import hashlib
import hmac
import secrets

from deluge.error import InvalidHashError

SALT_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def gen_salt(length: int) -> str:
    """Generate a random string of SALT_CHARS with specified ``length``."""
    if length <= 0:
        raise ValueError('Salt length must be at least 1.')

    return ''.join(secrets.choice(SALT_CHARS) for _ in range(length))


def _hash_internal(method: str, salt: str, password: str) -> tuple[str, str]:
    method, *args = method.split('$')
    salt_bytes = salt.encode()
    password_bytes = password.encode()

    if method == 'scrypt':
        if not args:
            n = 2**15
            r = 8
            p = 1
        else:
            try:
                n, r, p = map(int, args)
            except ValueError:
                raise ValueError("'scrypt' takes 3 arguments.") from None

        maxmem = 132 * n * r * p  # ideally 128, but some extra seems needed
        return (
            hashlib.scrypt(
                password_bytes, salt=salt_bytes, n=n, r=r, p=p, maxmem=maxmem
            ).hex(),
            f'scrypt${n}${r}${p}',
        )

    else:
        raise ValueError(f"Invalid hash method '{method}'.")


def generate_password_hash(
    password: str, method: str = 'scrypt', salt_length: int = 16
) -> str:
    """Securely hash a password for storage. A password can be compared to a stored hash using check_password_hash.

    Args:
        password (str): The plaintext password to hash.
        method (str): The key derivation function and parameters. Defaults to 'scrypt'.
        salt_length (int): The length of the salt to generate. Defaults to 16.

        Returns:
            str: The hashed password in the format '$method$salt$hash'.

    """
    salt = gen_salt(salt_length)
    h, actual_method = _hash_internal(method, salt, password)
    return f'${actual_method}${salt}${h}'


def check_password_hash(pwhash: str, password: str) -> bool:
    """Securely check that the given stored password hash, previously generated using
    generate_password_hash, matches the given password.

    Methods may be deprecated and removed if they are no longer considered secure. To
    migrate old hashes, you may generate a new hash when checking an old hash, or you
    may contact users with a link to reset their password.

    Args:
        pwhash (str): The hashed password in the format '$method$salt$hash
        password (str): The plaintext password to check against the hash.

    Raises:
        ValueError: If the hash format is invalid or the method is not recognized.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    method = None
    try:
        method, salt, stored_hash = pwhash.lstrip('$').rsplit('$', 2)
        computed_hash = _hash_internal(method, salt, password)[0]
    except ValueError as ve:
        raise InvalidHashError(
            'Invalid password hash format. Expected format: "$method$salt$hash".',
            method=method if method else pwhash,
        ) from ve

    return hmac.compare_digest(computed_hash, stored_hash)
