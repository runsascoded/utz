# S3 utilities:
#
# - `client()`: cached boto3 S3 client
# - `parse_bkt_key(args: tuple[str, ...]) -> tuple[str, str]`: parse bucket and key from s3:// URL or separate arguments
# - `get_etag(*args: str, err_ok: bool = False, strip: bool = True) -> str | None`: get ETag of S3 object
# - `get_etags(*args: str) -> dict[str, str]`: get ETags for all objects with the given prefix
# - `atomic_edit(...) -> Iterator[str]`: context manager for atomically editing S3 objects

from __future__ import annotations

import re
from contextlib import contextmanager
from functools import cache
from os import getcwd, path
from os.path import exists, join
from tempfile import TemporaryDirectory
from typing import Iterator

import boto3
from botocore.exceptions import ClientError

from utz import Log, err, silent


@cache
def client():
    return boto3.client('s3')


def parse_bkt_key(args: tuple[str, ...]) -> tuple[str, str]:
    if len(args) == 1:
        arg = args[0]
        if arg.startswith('s3://'):
            arg = arg[len('s3://'):]
        bkt, key = arg.split('/', 1)
    elif len(args) == 2:
        bkt, key = args
    else:
        raise ValueError('Too many arguments')
    return bkt, key


def get_etag(
    *args: str,
    err_ok: bool = False,
    strip: bool = True,
) -> str | None:
    """
    Get the ETag of an S3 object.

    Args:
        args (str): The full s3:// URL of the object, or the bucket and key as separate arguments
        err_ok (bool): If True, return None instead of raising FileNotFoundError if object doesn't exist
        strip (bool): If True, strip quotes from ETag

    Returns:
        str: The ETag value of the S3 object, or None if it doesn't exist (and err_ok=True)
    """
    bkt, key = parse_bkt_key(args)
    s3 = client()

    try:
        res = s3.head_object(Bucket=bkt, Key=key)
        etag = res.get('ETag', '')
        if strip:
            etag = etag.strip('"')
        return etag
    except ClientError as e:
        if e.response['Error']['Code'] != '404':
            raise
        if not err_ok:
            raise FileNotFoundError(f"Object {bkt}/{key} does not exist")
        return None


def get_etags(*args: str) -> dict[str, str]:
    """Return etags for all objects with the given prefix.

    Args:
        args (str): The full s3:// URL of the object, or the bucket and key as separate arguments

    Returns:
        dict[str, str]: A mapping of object keys to ETags
    """
    bkt, key = parse_bkt_key(args)
    s3 = client()
    res = s3.list_objects_v2(Bucket=bkt, Prefix=key)
    etags = {
        obj['Key']: obj['ETag'].strip('"')
        for obj in res.get('Contents', [])
    }
    return etags


class ETagConflictError(RuntimeError):
    """ETag has changed, indicating conflicting updates"""
    pass


class ConditionalRequestError(RuntimeError):
    """Concurrent conflicting operation detected"""
    pass


@contextmanager
def atomic_edit(
    bucket_or_url: str,
    key: str | None = None,
    *,
    s3 = None,
    create_ok: bool = False,
    download: bool | None = None,
    rm_ok: bool = False,
    basename: str | None = None,
    keep: bool = False,
    log: Log = err,
    dry_run: bool = False,
    **kwargs
) -> Iterator[str]:
    """
    Context manager for atomically editing S3 objects with optimistic locking.
    Yields a path in a temporary directory. If a file is created at that path,
    it will be conditionally uploaded to S3 on exit.

    Args:
        bucket_or_url: Either bucket name or full s3:// URL
        key: Optional object key (required if bucket_or_url is bucket name)
        s3: Optional S3 client
        create_ok: If True, allows creation of new objects
        download: If True, download object to temp path before yielding
        rm_ok: If True, delete object if temp path is removed. Implies download=True, unless download=False is passed explicitly.
        basename: Optional name for temp file (defaults to key basename)
        keep: If True, don't delete temp file on exit
        log: Optional logger function
        dry_run: If True, don't actually upload (or delete) the modified file
        **kwargs: Additional arguments to pass to put_object

    Yields:
        Path in temporary directory where file can be created

    Raises:
        ETagConflictError: If ETag has changed (HTTP 412)
        ConditionalRequestError: If concurrent conflict (HTTP 409)
        ClientError: For other S3 errors
        FileNotFoundError: If create_ok=False and object doesn't exist
        ValueError: If URL is invalid or key is missing
    """
    log = log or silent

    if not s3:
        s3 = client()

    # Parse bucket and key from args
    if key is None:
        match = re.match(r's3://([^/]+)/(.+)', bucket_or_url)
        if not match:
            raise ValueError("Single argument must be s3:// URL")
        bkt, key = match.groups()
    else:
        bkt = bucket_or_url

    url = f"s3://{bkt}/{key}"
    # Get current etag if object exists
    etag0 = get_etag(bkt, key, err_ok=create_ok, strip=False)

    with TemporaryDirectory(dir=getcwd()) as tmpdir:
        tmp_path = join(tmpdir, basename or path.basename(key))
        if download or (rm_ok and download is not False):
            log(f"Downloading {url} to {tmp_path}")
            s3.download_file(bkt, key, tmp_path)

        yield tmp_path

        if exists(tmp_path):
            if etag0:
                kwargs['IfMatch'] = etag0

            try:
                if dry_run:
                    log(f"Dry run: would upload {tmp_path} to {url}")
                    etag1 = get_etag(bkt, key, err_ok=create_ok, strip=False)
                    if etag0 != etag1:
                        raise ETagConflictError(f"ETag mismatch: {etag0} != {etag1}")
                else:
                    with open(tmp_path, 'rb') as f:
                        s3.put_object(
                            Bucket=bkt,
                            Key=key,
                            Body=f,
                            **kwargs
                        )
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'PreconditionFailed':
                    raise ETagConflictError("ETag mismatch - object was modified") from e
                if error_code == 'ConditionalRequestFailed':
                    raise ConditionalRequestError("Concurrent conflicting operation") from e
                raise
        else:
            if rm_ok:
                if dry_run:
                    log(f"Would delete {url}")
                else:
                    log(f"Deleting {url}")
                    s3.delete_object(Bucket=bkt, Key=key)
