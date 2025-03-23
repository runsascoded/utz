from __future__ import annotations

from contextlib import contextmanager
import tempfile
from pathlib import Path
import re

from utz import Log, err


class ETagConflictError(RuntimeError):
    """ETag has changed, indicating conflicting updates"""
    pass


class ConditionalRequestError(RuntimeError):
    """Concurrent conflicting operation detected"""
    pass


@contextmanager
def s3_atomic_edit(
    bucket_or_url: str,
    key: str | None = None,
    *,
    s3 = None,
    create_ok: bool = False,
    download: bool | None = None,
    rm_ok: bool = False,
    basename: str | None = None,
    log: Log = err,
    **kwargs
):
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
    from boto3 import client
    from botocore.exceptions import ClientError

    if not s3:
        s3 = client('s3')

    # Parse bucket and key from args
    if key is None:
        match = re.match(r's3://([^/]+)/(.+)', bucket_or_url)
        if not match:
            raise ValueError("Single argument must be s3:// URL")
        bucket, key = match.groups()
    else:
        bucket = bucket_or_url

    url = f"s3://{bucket}/{key}"
    # Get current etag if object exists
    try:
        head = s3.head_object(Bucket=bucket, Key=key)
        etag = head['ETag']
    except ClientError as e:
        if e.response['Error']['Code'] != '404':
            raise
        if not create_ok:
            raise FileNotFoundError(f"Object {bucket}/{key} does not exist")
        etag = None

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / (basename or Path(key).name)
        if download or (rm_ok and download is not False):
            log(f"Downloading {url} to {tmp_path}")
            s3.download_file(bucket, key, str(tmp_path))

        yield tmp_path

        if tmp_path.exists():
            if etag:
                kwargs['IfMatch'] = etag

            try:
                with open(tmp_path, 'rb') as f:
                    s3.put_object(
                        Bucket=bucket,
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
                log(f"Deleting {url}")
                s3.delete_object(Bucket=bucket, Key=key)
