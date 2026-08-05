# Live-endpoint test scaffolding for `utz.s3` (S3 + R2)

Status: **done — R2 live run green** (2026-08-05, ctbk session; suite + src changes landed 2026-08-04). All 8 tests pass against R2 (`--profile cf`, `s3://ctbk/tmp/utz-s3-tests`), including the conflict and create-race paths. See Findings below. Motivation: pyrmts' shard-invalidation journal wants `atomic_edit`-style CAS (If-Match conditional PUT) against Cloudflare R2; R2's S3 shim claims conditional-write support but the 412 path has never been exercised by us. `utz.s3` currently has zero test coverage (no `test/test_s3.py`, no moto, no live gating).

## Shape

Env-gated live tests, endpoint-parameterized so one suite runs against both AWS S3 and R2:

- `UTZ_S3_TEST_URL` — `s3://bucket/prefix` to test under; suite skips (`pytest.mark.skipif`) when unset. Creds/endpoint via the standard boto3 env (`AWS_ENDPOINT_URL` for R2, or a profile). Keys created under a per-run uuid subprefix, deleted in teardown.
- Marker `live` (register in `pytest.ini`), so `pytest -m 'not live'` stays hermetic in CI.
- Optionally a second env `UTZ_S3_TEST_URL_R2` so one invocation can sweep both backends; otherwise run twice with different env.

## Tests to lock

1. `get_etag` / `get_etags`: roundtrip after `put_object`, `err_ok` on missing key.
2. `atomic_edit` happy path: download → mutate → conditional put lands; etag changes.
3. **`atomic_edit` conflict path (the point)**: enter the context, mutate the object out-of-band (second client), exit → `ETagConflictError` from HTTP 412. This is the R2 If-Match verification pyrmts needs.
4. `create_ok=True` on a missing key: creates; and two racing creators → second gets the conflict (If-None-Match path, if/when `atomic_edit` grows it — today creation is unconditional, worth tightening while here).
5. `rm_ok`: removing the temp file deletes the object.
6. `dry_run`: no write occurs; stale-etag detection still raises.

Assertion style per global CLAUDE.md: exact equality on contents/etags, no substring `in` checks.

## Implementation notes (2026-08-04)

- Suite: `test/test_s3.py`, all tests marked `live` (registered in `pytest.ini`), parameterized over backends `['s3', 'r2']` via a `backend` fixture yielding `(client, bucket, per-test-uuid-prefix)`; teardown `delete_objects` under the prefix.
- Env: `UTZ_S3_TEST_URL` / `UTZ_S3_TEST_URL_R2` as specced; each backend also honors optional companions `UTZ_S3_TEST_PROFILE[_R2]` (boto3 profile; can carry `endpoint_url` in `~/.aws/config`) and `UTZ_S3_TEST_ENDPOINT[_R2]` (explicit `endpoint_url`), since a dual-backend sweep needs per-backend clients that the ambient boto3 env can't express.
- Src changes to `utz/s3.py` that came up:
  - `get_etag` / `get_etags` grew an `s3=` kwarg, and `atomic_edit` now threads its `s3` client into its internal `get_etag` calls — previously the entry/dry-run HEADs always used the global cached `client()`, silently ignoring a caller-passed client (would have hit the wrong endpoint entirely for R2).
  - Spec item 4's tightening: when the object didn't exist on entry (`create_ok=True`), the exit PUT now sends `If-None-Match: *`, so racing creators conflict instead of last-writer-wins. A 412 on that path raises `ETagConflictError("Object was created concurrently")` (vs `"ETag mismatch - object was modified"` on the `If-Match` path).
  - `dry_run` stale-check now HEADs with `err_ok=True`, so out-of-band *deletion* during an edit also surfaces as `ETagConflictError` (was `FileNotFoundError`).
- Hermetic verification: `pytest test/test_s3.py -m 'not live'` → 16 deselected; with env unset → 16 skipped; full suite unaffected.

## Findings (R2 live run, 2026-08-05)

- **R2 PutObject honors both `If-Match` and `If-None-Match: *`, returning HTTP 412 with error code `PreconditionFailed`** — byte-identical to AWS's code string. Verified two ways: the full suite (`UTZ_S3_TEST_URL_R2='s3://ctbk/tmp/utz-s3-tests' UTZ_S3_TEST_PROFILE_R2=cf pytest test/test_s3.py` → 8 passed, 8 skipped [s3 backend unset]), and a direct boto3 probe printing `e.response['Error']['Code']` for both a stale-`IfMatch` PUT and an `IfNoneMatch='*'` PUT over an existing key.
- No except-arm changes needed in `atomic_edit`: the existing `PreconditionFailed` handling covers R2 as-is.
- This is the verification pyrmts' shard-invalidation journal was gated on (`~/c/pyrmts/specs/shard-invalidation.md`): `atomic_edit`-style CAS against R2 is safe to take prod traffic.
- The `s3` (AWS) backend sweep remains unexercised live; run when convenient with `UTZ_S3_TEST_URL` set — no known risk, R2 was the open question.
