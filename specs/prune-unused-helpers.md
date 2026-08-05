# Prune unused `utz` helper modules (deferred candidates)

Status: **open** (2026-08-04). Follow-up to the gsmo/`utz.setup`/`git.clone.tmp`+`git.txn` removals; these candidates were surveyed at the same time but deliberately deferred.

## Survey method + caveat

`rg` over `.py` files under `~/c` on this laptop (see `tmp/utz-usage-survey` from that session) for `from utz.<mod>` / `from utz import … <mod>` / `utz.<mod>` imports. **Not covered**: notebooks, other machines (EC2 nodes), ad hoc REPL usage, and any external `utz` consumers on PyPI.

## Zero local users (rm candidates)

- `utz.docker` (whole subpackage; gsmo-era Dockerfile-builder DSL) + `test_docker.py`
- `utz.pdf`
- `utz.sql`
- `utz.ssh`
- `utz.pnds`
- `utz.df_counts`
- `utz.diff_dfs`
- `utz.parallel`

## Single local users (keep, noted for reference)

- `utz.plots` ← `hccs/path/path_data/months.py`
- `utz.mem` ← `disk-tree/src/disk_tree/cli/index.py`

## Also spotted, not yet decided

- `utz.git._checkout` / `git.checkout`: only referenced by `utz/git/__init__.py` itself; no external users found in the survey (which targeted module imports, not attribute access — DC before removing).
