# Live-endpoint test scaffolding for `utz.s3` (S3 + R2)

Status: **open** (2026-08-04, written from the pyrmts session). Motivation: pyrmts' shard-invalidation journal wants `atomic_edit`-style CAS (If-Match conditional PUT) against Cloudflare R2; R2's S3 shim claims conditional-write support but the 412 path has never been exercised by us. `utz.s3` currently has zero test coverage (no `test/test_s3.py`, no moto, no live gating).

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

## Notes

- Findings from the R2 run (esp. whether PutObject honors `If-Match` and returns 412, and the exact error code string boto3 surfaces — AWS uses `PreconditionFailed`, R2 may differ) should be recorded here; pyrmts will consume `atomic_edit` for its R2-resident invalidation journal on the strength of that result.
- If R2 surfaces a different error code than `PreconditionFailed`/`ConditionalRequestFailed`, extend the except-arm in `atomic_edit` accordingly (that's a src change, in-scope for this spec).
