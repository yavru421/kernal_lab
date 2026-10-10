# kernel_lab — Project Rules

Purpose: work ON CUDA kernels (build, benchmark, validate, improve) and LOG every use of them.
This project does not own subject work (bowling, cinema, GVSM). Those projects call kernels; kernel_lab records and verifies it.

Global Metropolis rules still apply (substrate_autonomy, banned_software, mcp_routing, duckdb_cuda_acceleration, mind_lake, operator_rails, strict_versioning).
Governed by the **Substrate Autonomy & Laboratory Velocity Doctrine**: *"Human possible without AI agents; human impractical without AI agents."* (See [SUBSTRATE_AUTONOMY_DOCTRINE.md](file:///c:/dev/docs/SUBSTRATE_AUTONOMY_DOCTRINE.md)).

Project-specific invariants:

1. **Ledger first.** Every kernel build, run and operator verdict becomes a row in `kernel_lab.duckdb` (schema: `sql/001_schema.sql`). No run counts as done until it is logged.
2. **Verdicts are data.** When John says a result is good or garbage, write a `verdicts` row against the run. Never edit the run row.
3. **Exact traces.** Store compiler, driver and runtime errors verbatim in `error_trace`. No summaries.
4. **No per-subject scripts.** Anything that runs a kernel goes through one registered path (see `docs/PATHS.md`). No inline Python, no ctypes one-offs, no throwaway inspection scripts.
5. **Reference, don't copy.** `kernels.source_path` points at the owning repo. Consolidation is a later decision, made from ledger evidence.
6. **Run folders.** Each run writes to `runs/<run_id>/` with its own manifest and outputs. No loose files in `C:\tmp`.
7. **Versioning.** New attempt = new run_id and, for docs, the next `_vN` file. Never overwrite a prior run or doc.
8. **GPU truth.** Record `nvidia-smi` state and kernel `gpu_ms` vs `wall_ms` on every run. A kernel that is not on the GPU is a defect to log, not hide.
9. **Zero CPU fallbacks hidden in wrappers.** If a wrapper touches pixels on the CPU, log it as a defect against that kernel.

Database queries use time windows or aggregates. No blind `LIMIT 5/10/20`.
