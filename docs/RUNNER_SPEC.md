# RUNNER_SPEC v1 — Option B: registered kernel runner

Status: DRAFT for John's review. Nothing here is built yet.
Scope: one native host that loads C-ABI CUDA DLLs from `kernels.dll_path`, runs one kernel call, writes `runs/<run_id>/`, and logs to `kernel_lab.duckdb` itself. No Python wrapper layer, no ctypes, no per-subject scripts.

## 1. Components

| Piece | Form | Responsibility |
|---|---|---|
| `kernel_host.exe` | C++17, MSVC 14.44 + CUDA 12.6 runtime, links `duckdb.dll` (C API) | Load DLL, resolve symbol, time, capture errors, write run folder, insert ledger rows |
| `kernel_lab` MCP tools | Two tools registered on `workspace-execution-mcp-server` (thin: spawn `kernel_host.exe` with argv, return its stdout JSON) | `kernel_run`, `kernel_verdict` |
| Adapters | `adapters/<kernel_id>.json` (data, not code) | Describe symbol, argument layout, input decoder, output encoder for each kernel |

The MCP layer never touches pixels or buffers. All work happens in `kernel_host.exe`.

## 2. Tool signatures

### `kernel_run`
```jsonc
{
  "kernel_id": "cu_geopin_solver",        // required, FK kernels.kernel_id
  "input":     "C:\\footage\\backup.MOV",   // required, file path (video, image dir, .bin, .npy-free raw)
  "params":    { "pins": [[412,233],[640,310]], "patch": 21 },  // required, adapter-validated
  "caller":    "cu_vision_lite",          // required, who is invoking
  "subject":   "bowling",                 // required, what it is pointed at
  "build_id":  null,                      // optional, pin to a builds row; default = latest ok build or registry dll_path
  "golden_id": null,                      // optional, marks this as a regression run (Option C)
  "nsys":      false,                     // optional, Option E flag: wrap in nsys profile
  "timeout_s": 600                        // optional, hard kill; recorded as error
}
```
Returns (always, success or failure):
```jsonc
{ "run_id": "20261003T101500_cu_geopin_solver_001", "ok": true,
  "gpu_ms": 182.4, "wall_ms": 941.0, "frames": 300, "vram_peak_mb": 612,
  "run_dir": "c:\\dev\\kernel_lab\\runs\\20261003T101500_cu_geopin_solver_001\\",
  "outputs": [ { "path": "...\\track.json", "kind": "telemetry_json", "sha256": "..." } ],
  "error_trace": null }
```

### `kernel_verdict`
```jsonc
{ "run_id": "20261003T101500_cu_geopin_solver_001",  // required, must exist in runs
  "verdict": "garbage",                              // great | good | meh | garbage | wrong_tool
  "note": "drifts off the ball after frame 140",     // optional, John's words verbatim
  "source": "operator" }                             // operator | agent_check
```
Inserts one `verdicts` row. Never updates `runs`. Rejects an unknown `run_id` and an unknown verdict value.

## 3. run_id and run folder

`run_id = <yyyymmddThhmmss>_<kernel_id>_<seq3>`, local time, `seq` = 1 + count of runs with that prefix second. The folder is created before the DLL is loaded so that load failures are recorded too.

```
runs/<run_id>/
  manifest.json      # written twice: status "started" at t0, rewritten as "finished"/"failed" at end
  stdout.log         # host + kernel stdout
  stderr.log         # host + kernel stderr, verbatim
  nvidia_smi_pre.csv
  nvidia_smi_post.csv
  outputs/           # every artifact the adapter emits; nothing written outside this folder
  nsys/              # only when nsys=true (.nsys-rep)
```

### manifest.json
```jsonc
{
  "schema": "kernel_lab.manifest/v1",
  "run_id": "...", "status": "finished",            // started | finished | failed | timeout
  "kernel": { "kernel_id": "...", "dll_path": "...", "dll_sha256": "...", "symbol": "cu_geopin_track_step",
              "build_id": "...", "adapter": "adapters/cu_geopin_solver.json", "adapter_sha256": "..." },
  "invocation": { "caller": "...", "subject": "...", "params": { }, "golden_id": null,
                  "host_argv": [ "kernel_host.exe", "..." ] },
  "input":  { "path": "...", "sha256": "...", "bytes": 0, "frames": 300, "decoder": "nvdec" },
  "gpu":    { "pre":  { "name": "...", "driver": "616.92", "mem_used_mib": 1568, "temp_c": 46, "util_pct": 0 },
              "post": { } , "device_index": 0, "compute_cap": "8.9" },
  "timing": { "ts_start": "...", "ts_end": "...", "wall_ms": 0, "gpu_ms": 0,
              "gpu_ms_per_call": [ ], "h2d_ms": 0, "d2h_ms": 0, "calls": 0 },
  "memory": { "vram_peak_mb": 0 },
  "outputs": [ { "path": "outputs/track.json", "kind": "telemetry_json", "bytes": 0, "sha256": "..." } ],
  "defects": [ ],                                   // e.g. "cpu_pixel_touch: adapter decoded on CPU"
  "error":  { "stage": null, "code": null, "trace": null }
}
```

## 4. Timing: gpu_ms vs wall_ms

- **wall_ms**: `QueryPerformanceCounter` from the moment the host process starts the run (before `LoadLibraryW`) to after the last output is hashed. Includes decode, H2D/D2H, file I/O.
- **gpu_ms**: sum of `cudaEventElapsedTime` across all kernel calls. The host records `cudaEventRecord(start, stream)` / `(stop, stream)` around every DLL call on a stream it owns and passes to the DLL when the signature takes `cudaStream_t`.
  - If a DLL entrypoint takes no stream (uses the legacy default stream internally), events are recorded on stream 0 and the manifest flags `"timing_mode": "default_stream"`. That is less precise and gets logged as a defect against the kernel.
- **h2d_ms / d2h_ms**: event-timed separately when the host does the copies.
- **Ratio check**: if `gpu_ms / wall_ms < 0.05` on a non-trivial input, a `defects` entry `low_gpu_share` is written. AGENTS.md §8: a kernel that is not on the GPU is a defect to log.
- **CPU pixel touch** (AGENTS.md §9): adapters declare `decoder` and `encoder`. Anything other than `nvdec` / `nvenc` / `device_buffer` adds a `cpu_pixel_touch` defect. Example: a raw file read is fine, a CPU resize is not.
- **vram_peak_mb**: `cudaMemGetInfo` sampled before, after, and from a 50 ms watcher thread; peak minus pre-run baseline.

## 5. Error capture (verbatim, never summarized)

Every failure maps to `error.stage` plus the exact text, written to `manifest.json`, `stderr.log` and `runs.error_trace`:

| stage | Source of text |
|---|---|
| `resolve` | kernel_id missing from registry / dll_path NULL / adapter missing |
| `load` | `LoadLibraryExW` failure: `GetLastError()` + `FormatMessageW` text + DLL path (catches missing cudart64_12.dll etc.) |
| `symbol` | `GetProcAddress` failure: symbol name + `GetLastError()` text |
| `input` | decoder error string (NVDEC `CUresult` name + `cuGetErrorString`) |
| `kernel_return` | non-zero int return from the DLL entrypoint, raw value, plus adapter's code map if any (e.g. `-2 = cudaMalloc queries failed`) |
| `cuda` | `cudaGetLastError()` + `cudaPeekAtLastError()` after each call: `cudaGetErrorName` + `cudaGetErrorString` |
| `crash` | SEH `__try/__except` around the call: exception code (e.g. `0xC0000005`) + faulting address + module from `GetModuleHandleEx`; minidump written to `runs/<run_id>/crash.dmp` |
| `timeout` | watchdog kill after `timeout_s`; last stdout line |
| `ledger` | DuckDB C API `duckdb_query` error string; host also writes it to `stderr.log` so the run folder survives a ledger failure |

Rules: `ok = false` on any stage. No retry inside the host. No fallback to another DLL or to a CPU path. The tool returns the error JSON to the caller unchanged.

## 6. Ledger writes (single transaction at end)

1. At start: `INSERT INTO runs (run_id, ts_start, kernel_id, caller, subject, input_path, params_json, run_dir)` with `ok = NULL`, so a crashed host still leaves a row.
   *Open point:* this means one later fill-in of the same row. AGENTS.md says "never edit the run row". Options: (a) allow exactly one completion write by the host, or (b) add a `run_events` append-only table (`started`, `finished`) and derive `runs` as a view. **John to pick.**
2. At end: `ts_end, ok, gpu_ms, wall_ms, vram_peak_mb, frames, input_sha256, error_trace, nsys_report`.
3. One `outputs` row per file in `outputs/` (+ `stdout.log`/`stderr.log` as `kind='log'`).
4. Defects: proposed new table `defects(defect_id, run_id, kernel_id, kind, detail, ts)`. Needs a schema migration as `sql/030_defects_v1.sql`.

## 7. Adapter file (data-only, one per kernel)

```jsonc
{ "kernel_id": "cu_geopin_solver",
  "dll_symbol_init": "cu_geopin_init",
  "dll_symbol_step": "cu_geopin_track_step",
  "signature": "int(const uint8_t* d_frame, int w, int h, float* d_pins, int n_pins, int patch, cudaStream_t)",
  "decoder": "nvdec", "per": "frame",
  "params_schema": { "pins": "float2[]", "patch": "int" },
  "outputs": [ { "name": "track.json", "kind": "telemetry_json", "from": "d_pins per frame" } ],
  "return_codes": { "0": "ok" } }
```
The host ships a fixed set of call shapes (`per_frame_image`, `per_buffer`, `init_step_release`, `batch_vector`). An adapter picks one. A new shape means a host change and a version bump, not a script.

## 8. Not in v1

- No kernel that only exists as an ATen/c10 `.pyd` (`screen_kernel`, `object_clear`, `diff_embed_kernel`). The runner refuses them with `stage=resolve, trace="no C-ABI export"`.
- No multi-GPU, no remote execution.
- Nsight (`nsys=true`) is spec'd as a flag only. Implementation follows Option E.

## 9. Decisions needed from John

1. Run-row completion: host completion write (a) vs `run_events` table (b).
2. Approve the `defects` table.
3. First three adapters: `cu_geopin_solver`, `cu_skeleton_kinematics`, `adaptive_delta_fused` (per PATHS.md order)?
4. Host location: `c:\dev\kernel_lab\host\` (inside this repo, since it is lab tooling, not a kernel).
