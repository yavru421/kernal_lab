@Conversation [CUDA Kernel Lab — Identity Review and Project Setup - ID: 2199999b-c84c-4dca-b0aa-8bfbca4586b4]

**Workspace**: `c:\dev\kernel_lab` (kernels live in other repos under `c:\dev`; reference them, do not copy)
**Current Milestone**: Scaffolded `kernel_lab`: `kernel_lab.duckdb` with tables `kernels, builds, runs, outputs, verdicts, golden_inputs`, views `v_kernel_usage, v_never_run, v_unbuilt, v_verdict_rate, v_run_latest_verdict`. 30 `.cu` kernels from 14 repos registered, 0 runs logged. Findings behind this project: `cu_vision_lite` outputs are tracked/edited video plus per-video telemetry JSON, mostly scattered in `C:\tmp`; `duckdb_cuda_acceleration.md` routes "Visual Diffing & Frame Tracking" to `workspace_cuda_diff`, whose schema is an AST-token and embedding diff (`diff_embed_cuda.pyd`), not a frame diff; footage work therefore had no registered tool and ran as per-video scripts.
**Active Files**: `AGENTS.md`, `docs/PATHS.md`, `sql/001_schema.sql`, `sql/002_seed_kernels.sql`, `sql/010_views.sql`, `kernel_lab.duckdb`

**Immediate Objective**: Read `AGENTS.md` and `docs/PATHS.md`, then do these in order without asking preamble questions:
1. Backfill the registry. For each of the 30 kernels, find any built DLL in its repo (Everything index, port 7999), and record `dll_path`. Read exported C symbols with `dumpbin /exports` via `workspace_exec_array` and write them to `exports`. Report exact errors verbatim. Show `v_unbuilt` before and after.
2. Diff the duplicates: `cu_geopin_solver` (cu_vision_lite vs cuda_pin_tracker) and `diff_embed_kernel` (diff_embed_cuda vs turbo-cuda-duckdb). Use a byte/line diff, not the text-embedding tool. Record which copy is canonical in `kernels.notes`.
3. Check `nvidia-smi` and `nvcc --version`, and record the baseline in a first `builds` row for `cu_vision_lite` (rebuild `cu_vision_lite_sm89.dll` only if a build script already exists; do not invent one).
4. Draft Option B from `docs/PATHS.md` as `docs/RUNNER_SPEC.md`: tool signature for `kernel_run` and `kernel_verdict`, the `runs/<run_id>/manifest.json` layout, and how errors and `gpu_ms` vs `wall_ms` are captured. Native host only, no Python wrapper layer. Stop at the spec for John's review.

Rules for this chat: log every kernel invocation to the ledger, record John's verdicts as `verdicts` rows, no per-subject scripts, no blind LIMITs, and write new versions instead of overwriting.
