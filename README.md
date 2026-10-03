# kernel_lab

Workbench and usage ledger for the machine's CUDA kernels (RTX 4060, AD107 / SM_89).

- `kernel_lab.duckdb` — the ledger (kernels, builds, runs, outputs, verdicts, golden_inputs).
- `sql/` — schema (`001`), kernel seed (`002`), views (`010`). Re-runnable.
- `runs/` — one folder per logged run: `runs/<run_id>/`.
- `golden/` — fixed inputs for regression comparison across builds.
- `docs/PATHS.md` — options and recommended order.
- `docs/FRESH_FIRST_PROMPT.md` — first prompt for the first chat in this folder.
- `AGENTS.md` — project rules.

## Query the ledger
```
duckdb c:\dev\kernel_lab\kernel_lab.duckdb -c "SELECT * FROM v_kernel_usage ORDER BY runs DESC"
```
Other views: `v_never_run`, `v_unbuilt`, `v_verdict_rate`, `v_run_latest_verdict`.

## Rebuild from scratch
Run `sql/001_schema.sql`, `sql/002_seed_kernels.sql`, `sql/010_views.sql` in order against a new `kernel_lab.duckdb`.

## Status
Scaffold only. 30 kernels registered, 0 runs. No kernel has been built or executed from this project yet.
