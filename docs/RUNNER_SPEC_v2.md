# RUNNER_SPEC v2 — Option B: registered kernel runner

Supersedes [RUNNER_SPEC.md](RUNNER_SPEC.md) (v1, kept for diff). Status: skeleton built, no kernel invoked yet.

## Decisions applied (John, 2026-10-03)
| §9 item | Decision | Where |
|---|---|---|
| Run-row completion | (b) append-only `run_events`; `runs` is a view | `sql/030_run_events_defects_v1.sql` |
| Defects table | Approved, seeded with 10 findings (3 blockers) | same |
| First adapters | `cu_geopin_solver` → `cu_skeleton_kinematics` → `adaptive_delta_fused` | `host/adapters/*.json` |
| Host location | `kernel_lab/host/` | `host/` |
| `.pyd` kernels | No shims. `defects.kind='banned_runtime_abi'`, `blocks_runner=true` | `v_open_blockers` |
| Unbuilt kernels | `dxgi_cuda_delta`, `pdf_preview_cuda` left unbuilt until host validated on the 3 adapters | — |

## Changes vs v1
1. **Ledger write path:** in-process DuckDB C API (libduckdb v1.5.6, matching `duckdb.exe` v1.5.6), with prepared statements and all parameters bound. The host spawns no `duckdb.exe`.
2. **GPU state:** NVML in-process (`nvmlDeviceGetMemoryInfo`, temperature, utilization, compute cap). No `nvidia-smi` subprocess. Stored verbatim in `run_events.gpu_state_pre/post` and in the manifest.
3. **Hashing:** BCrypt SHA-256 in-process (DLL and adapter).
4. **Events:** the host inserts `<run_id>:started` before `LoadLibraryExW`, then exactly one of `<run_id>:finished|failed`. A hard crash leaves only `started` and `runs.terminal_event = 'no_terminal_event'`. If the `started` insert itself fails, the host exits 3 and writes `stderr.log` in the run folder, with no orphan terminal row.
5. **timing_mode** is now per adapter: `host_stream` | `default_stream` | `internal_stream`. `adaptive_delta_fused` is `internal_stream`: its module owns a static `g_stream`, which is logged as a defect.
6. **Init-with-args guard:** the host refuses to call an init symbol through a zero-argument pointer when the adapter declares `init_args`. That applies to `cu_init_screen_engine(int,int)`. It fails with `stage=resolve` instead of undefined behaviour.

## Skeleton coverage (host 0.1.0)
| Stage | State |
|---|---|
| resolve (registry, adapter, SHA-256) | done |
| started event + manifest | done |
| load (`LoadLibraryExW` + `FormatMessage`) | done |
| symbol (every adapter symbol via `GetProcAddress`) | done |
| init call (SEH guard, cudaEvent timing, `cudaMemGetInfo` delta, every CUDA return checked) | done for zero-arg init |
| main-call shapes `init_step_release`, `per_buffer` | **not implemented**, returns `stage=resolve` |
| NVDEC input decode, outputs/ hashing, `outputs` rows | not implemented |
| `kernel_verdict` | ledger insert only (MCP registration pending) |
| nsys flag | not implemented |

Expected first-run results per adapter at 0.1.0:
- `cu_geopin_solver`: init `cu_geopin_init` runs, then `failed / resolve: shape 'init_step_release': init ok, main call not implemented`.
- `cu_skeleton_kinematics`: `failed / resolve: no symbol_init; main-only shapes not implemented`.
- `adaptive_delta_fused`: `failed / resolve: symbol_init cu_init_screen_engine takes (int width, int height)`.

Each of these is a real ledger row, a planned failure that is still a logged run.

## Runtime requirements
- `cudart64_12.dll` must resolve at load time: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin` on PATH, or copied beside the exe. The toolchain is not on PATH for `workspace_exec_array` (defect `20261003_env_toolchain_path`).
- `duckdb.dll` is copied to `host\bin\` by `build.cmd`.
- The ledger file must not be held open read-write by another process during a run.

## Next increments (in order)
1. Transcribe the full `cu_geopin_track_step` signature (source line 346 onward) and implement `init_step_release` with NVDEC gray8 decode. Golden clip still TBD.
2. `per_buffer` for `cu_skeleton_kinematics_device`.
3. Init-arg marshalling (`int,int`) plus `internal_stream` timing for `adaptive_delta_fused`.
4. Register `kernel_run` / `kernel_verdict` on `workspace-execution-mcp-server` as thin argv wrappers around `kernel_host.exe`.
