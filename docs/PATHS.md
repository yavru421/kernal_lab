# Paths Forward for kernel_lab

Goal: work ON the CUDA kernels and log every use. Starting state (2026-10-03): 30 `.cu` sources across 14 repos registered, 0 runs logged, 3 with a DLL path recorded. "Unbuilt" in `v_unbuilt` means no DLL recorded in the registry, not proven unbuilt. Other repos may already ship DLLs that are not mapped yet.

## Option A — Ledger only (smallest, done at scaffold)
Registry + runs + verdicts in `kernel_lab.duckdb`. Callers log manually through DuckDB.
- Gain: answers "what kernels exist, which ones do I use, which ones work" from data.
- Cost: logging depends on discipline. It will decay if the logging step is manual.

## Option B — Registered runner (recommended next)
One MCP tool, `kernel_run(kernel_id, input, params, caller, subject)`, that loads the C-ABI DLL, runs it, writes `runs/<run_id>/`, and inserts the `runs` and `outputs` rows itself. Plus `kernel_verdict(run_id, verdict, note)`.
- Gain: logging is automatic. Fixes the gap where footage work had no registered tool and fell into per-video scripts.
- Cost: needs a small native host (C++ exe or in-process MCP server) with no Python wrapper layer.

## Option C — Golden clips and regression bench
Pick 1–2 fixed inputs per kernel (`golden/`), record an English pass condition, and re-run on every build. Compare `gpu_ms`, output hash and verdict across builds.
- Gain: you can tell whether a rebuild made a kernel better or worse. Works well for the tracking drift (bowling ball) and the dolly zoom snap.
- Cost: needs choosing the clips and agreeing on pass conditions.

## Option D — Consolidate sources into one monorepo
Pull the 30 sources and 3 duplicates (`cu_geopin_solver`, `diff_embed_kernel`) under one tree with one build script and one C-ABI surface.
- Gain: one place to build and test. Removes duplicates.
- Cost: large churn. Do it after A–C produce evidence about which kernels matter.

## Option E — Kernel profiling pass
Nsight Systems traces per kernel, stored as `nsys_report` on the run. Highest value for `cu_adaptive_delta_fused` and the tracker.
- Gain: real GPU numbers, per kernel.
- Cost: slower runs. Best as a flag on B, not a separate path.

## Recommended order
1. A (done) → backfill `dll_path` and `exports` for kernels that already have DLLs.
2. B (runner + verdict tool), since it makes everything after it log itself.
3. C on three kernels first: `cu_geopin_solver`, `cu_skeleton_kinematics`, `adaptive_delta_fused`.
4. E as a runner flag.
5. D only after the ledger shows which kernels are used.

## Open questions for John
- Is `cuda_pin_tracker` the newer home of `cu_geopin_solver`, or a stale copy? The ledger holds both until a diff says.
- Which clips are the golden ones? Candidates: `bowling_jd2_tester2.MOV`, `backup.MOV`, the concrete float clip, `crows.MOV`.
- Should `cu_vision_lite` keep calling kernels directly, or switch to the runner once B exists?
