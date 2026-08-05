"""Live-endpoint tests for `utz.s3` (see `specs/s3-live-tests.md`).

Env-gated and endpoint-parameterized, so one suite runs against both AWS S3 and Cloudflare R2:

- `UTZ_S3_TEST_URL`: `s3://bucket[/prefix]` to test under; the `s3` backend skips when unset.
  Creds/endpoint come from the standard boto3 env (`AWS_ENDPOINT_URL`, `AWS_PROFILE`, etc.).
- `UTZ_S3_TEST_URL_R2`: optional second backend, so one invocation sweeps both. Its client is built
  from companion envs `UTZ_S3_TEST_PROFILE_R2` (boto3 profile, which may carry `endpoint_url` in
  `~/.aws/config`) and/or `UTZ_S3_TEST_ENDPOINT_R2` (explicit endpoint URL). The same companions
  (`UTZ_S3_TEST_PROFILE` / `UTZ_S3_TEST_ENDPOINT`) work for the `s3` backend, when the ambient boto3
  env isn't enough.

All keys are created under a per-test uuid subprefix, and deleted in teardown.
"""

import re
from os import environ, remove
from uuid import uuid4

import pytest
from pytest import fixture, mark, raises

boto3 = pytest.importorskip('boto3')

from utz.s3 import ETagConflictError, atomic_edit, get_etag, get_etags

pytestmark = mark.live

URL_VAR = 'UTZ_S3_TEST_URL'


@fixture(params=['s3', 'r2'])
def backend(request, tmp_path, monkeypatch):
    """Yield `(s3_client, bucket, prefix)` for a live backend, or skip if its env isn't set."""
    suffix = '' if request.param == 's3' else '_R2'
    url = environ.get(f'{URL_VAR}{suffix}')
    if not url:
        pytest.skip(f'{URL_VAR}{suffix} not set')
    match = re.fullmatch(r's3://(?P<bkt>[^/]+)/?(?P<prefix>.*?)/?', url)
    if not match:
        raise ValueError(f'Invalid {URL_VAR}{suffix}: {url}')
    bkt, base_prefix = match['bkt'], match['prefix']

    profile = environ.get(f'UTZ_S3_TEST_PROFILE{suffix}')
    endpoint = environ.get(f'UTZ_S3_TEST_ENDPOINT{suffix}')
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    s3 = session.client('s3', **({'endpoint_url': endpoint} if endpoint else {}))

    prefix = '/'.join(filter(None, [base_prefix, f'utz-s3-test-{uuid4().hex}']))
    # `atomic_edit` creates its TemporaryDirectory under cwd; keep that inside pytest's tmp_path
    monkeypatch.chdir(tmp_path)
    yield s3, bkt, prefix
    res = s3.list_objects_v2(Bucket=bkt, Prefix=f'{prefix}/')
    keys = [obj['Key'] for obj in res.get('Contents', [])]
    if keys:
        s3.delete_objects(Bucket=bkt, Delete={'Objects': [{'Key': key} for key in keys]})


def get_body(s3, bkt: str, key: str) -> bytes:
    return s3.get_object(Bucket=bkt, Key=key)['Body'].read()


def test_get_etags(backend):
    s3, bkt, prefix = backend
    key1 = f'{prefix}/a.txt'
    key2 = f'{prefix}/b/c.txt'
    etag1 = s3.put_object(Bucket=bkt, Key=key1, Body=b'aaa\n')['ETag']
    etag2 = s3.put_object(Bucket=bkt, Key=key2, Body=b'ccc\n')['ETag']

    assert get_etag(bkt, key1, s3=s3) == etag1.strip('"')
    assert get_etag(f's3://{bkt}/{key1}', s3=s3) == etag1.strip('"')
    assert get_etag(bkt, key1, strip=False, s3=s3) == etag1

    missing = f'{prefix}/missing.txt'
    assert get_etag(bkt, missing, err_ok=True, s3=s3) is None
    with raises(FileNotFoundError, match=f'^{re.escape(f"Object {bkt}/{missing} does not exist")}$'):
        get_etag(bkt, missing, s3=s3)

    assert get_etags(bkt, f'{prefix}/', s3=s3) == {
        key1: etag1.strip('"'),
        key2: etag2.strip('"'),
    }


def test_atomic_edit(backend):
    s3, bkt, prefix = backend
    key = f'{prefix}/file.txt'
    s3.put_object(Bucket=bkt, Key=key, Body=b'v1\n')
    etag0 = get_etag(bkt, key, s3=s3)
    with atomic_edit(bkt, key, s3=s3, download=True) as tmp_path:
        with open(tmp_path, 'rb') as f:
            assert f.read() == b'v1\n'
        with open(tmp_path, 'wb') as f:
            f.write(b'v2\n')
    assert get_body(s3, bkt, key) == b'v2\n'
    assert get_etag(bkt, key, s3=s3) != etag0


def test_atomic_edit_conflict(backend):
    """The point: out-of-band write between entry and exit ⟹ conditional PUT fails with HTTP 412."""
    s3, bkt, prefix = backend
    key = f'{prefix}/file.txt'
    s3.put_object(Bucket=bkt, Key=key, Body=b'v1\n')
    with raises(ETagConflictError, match=r'^ETag mismatch - object was modified$'):
        with atomic_edit(bkt, key, s3=s3, download=True) as tmp_path:
            s3.put_object(Bucket=bkt, Key=key, Body=b'v2\n')
            with open(tmp_path, 'wb') as f:
                f.write(b'v3\n')
    assert get_body(s3, bkt, key) == b'v2\n'


def test_atomic_edit_create(backend):
    s3, bkt, prefix = backend
    key = f'{prefix}/new.txt'
    assert get_etag(bkt, key, err_ok=True, s3=s3) is None
    with atomic_edit(bkt, key, s3=s3, create_ok=True) as tmp_path:
        with open(tmp_path, 'wb') as f:
            f.write(b'new\n')
    assert get_body(s3, bkt, key) == b'new\n'


def test_atomic_edit_create_race(backend):
    """Racing creators: If-None-Match ⟹ the second lander gets the conflict, doesn't clobber."""
    s3, bkt, prefix = backend
    key = f'{prefix}/race.txt'
    with raises(ETagConflictError, match=r'^Object was created concurrently$'):
        with atomic_edit(bkt, key, s3=s3, create_ok=True) as tmp_path:
            s3.put_object(Bucket=bkt, Key=key, Body=b'racer\n')
            with open(tmp_path, 'wb') as f:
                f.write(b'mine\n')
    assert get_body(s3, bkt, key) == b'racer\n'


def test_atomic_edit_rm(backend):
    s3, bkt, prefix = backend
    key = f'{prefix}/rm.txt'
    s3.put_object(Bucket=bkt, Key=key, Body=b'v1\n')
    with atomic_edit(bkt, key, s3=s3, rm_ok=True) as tmp_path:
        with open(tmp_path, 'rb') as f:
            assert f.read() == b'v1\n'
        remove(tmp_path)
    assert get_etag(bkt, key, err_ok=True, s3=s3) is None


def test_atomic_edit_dry_run(backend):
    s3, bkt, prefix = backend
    key = f'{prefix}/file.txt'
    etag0 = s3.put_object(Bucket=bkt, Key=key, Body=b'v1\n')['ETag']
    with atomic_edit(bkt, key, s3=s3, download=True, dry_run=True) as tmp_path:
        with open(tmp_path, 'wb') as f:
            f.write(b'v2\n')
    assert get_body(s3, bkt, key) == b'v1\n'
    assert get_etag(bkt, key, strip=False, s3=s3) == etag0


def test_atomic_edit_dry_run_stale(backend):
    s3, bkt, prefix = backend
    key = f'{prefix}/file.txt'
    etag0 = s3.put_object(Bucket=bkt, Key=key, Body=b'v1\n')['ETag']
    with raises(ETagConflictError) as exc_info:
        with atomic_edit(bkt, key, s3=s3, download=True, dry_run=True) as tmp_path:
            etag1 = s3.put_object(Bucket=bkt, Key=key, Body=b'v2\n')['ETag']
            with open(tmp_path, 'wb') as f:
                f.write(b'v3\n')
    assert str(exc_info.value) == f'ETag mismatch: {etag0} != {etag1}'
    assert get_body(s3, bkt, key) == b'v2\n'
