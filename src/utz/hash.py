from __future__ import annotations

import hashlib
from typing import Literal

HashName = Literal[
    'md5',
    'sha1',
    'sha224',
    'sha256',
    'sha384',
    'sha512',
    'blake2b',
    'blake2s',
    'sha3_224',
    'sha3_256',
    'sha3_384',
    'sha3_512',
    'shake_128',
    'shake_256',
]


def hash_file(
    path: str,
    hash_name: HashName = 'sha256',
    chunk_size: int | None = None,
) -> str:
    """Return the SHA-256 hash of the file at the given path."""
    try:
        hash_fn = getattr(hashlib, hash_name)
    except AttributeError:
        raise ValueError(f"Invalid hash name: {hash_name}")

    with open(path, 'rb') as f:
        if chunk_size:
            hash = hash_fn()
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hash.update(chunk)
        else:
            hash = hash_fn(f.read())
        return hash.hexdigest()
