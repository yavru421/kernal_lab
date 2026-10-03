-- 030_run_events_defects_v1.sql  (2026-10-03)
-- John's §9 decisions: (1b) append-only run_events, runs derived as a view; (2) defects table approved.
-- Pre-check at apply time: runs=0, outputs=0, verdicts=0. The old runs table is renamed, not dropped.
BEGIN TRANSACTION;

ALTER TABLE runs RENAME TO runs_table_v1_retired;   -- empty; kept for audit

-- Append-only. One 'started' row per run, at most one terminal row (finished | failed | timeout).
-- A crash leaves only 'started': that IS the record.
CREATE TABLE run_events (
    event_id      VARCHAR PRIMARY KEY,          -- <run_id>:<event>
    run_id        VARCHAR NOT NULL,
    event         VARCHAR NOT NULL CHECK (event IN ('started','finished','failed','timeout')),
    ts            TIMESTAMP NOT NULL DEFAULT now(),
    -- started payload
    kernel_id     VARCHAR,
    build_id      VARCHAR,
    dll_path      VARCHAR,
    dll_sha256    VARCHAR,
    symbol        VARCHAR,
    adapter_sha256 VARCHAR,
    caller        VARCHAR,
    subject       VARCHAR,
    input_path    VARCHAR,
    params_json   VARCHAR,
    golden_id     VARCHAR,
    run_dir       VARCHAR,
    host_version  VARCHAR,
    gpu_state_pre VARCHAR,                      -- nvidia-smi CSV verbatim
    -- terminal payload
    ok            BOOLEAN,
    input_sha256  VARCHAR,
    gpu_ms        DOUBLE,
    wall_ms       DOUBLE,
    vram_peak_mb  DOUBLE,
    frames        BIGINT,
    timing_mode   VARCHAR,                      -- host_stream | default_stream | internal_stream
    error_stage   VARCHAR,                      -- resolve | load | symbol | input | kernel_return | cuda | crash | timeout | ledger
    error_trace   VARCHAR,                      -- verbatim, never summarized
    nsys_report   VARCHAR,
    gpu_state_post VARCHAR
);

-- Same column contract as the retired table so 010 views keep working.
CREATE VIEW runs AS
WITH s AS (SELECT * FROM run_events WHERE event = 'started'),
     t AS (SELECT * FROM run_events WHERE event IN ('finished','failed','timeout'))
SELECT s.run_id,
       s.ts            AS ts_start,
       t.ts            AS ts_end,
       s.kernel_id, s.caller, s.subject, s.input_path,
       t.input_sha256, s.params_json,
       t.ok,            -- NULL = no terminal event (crash / still running)
       t.gpu_ms, t.wall_ms, t.vram_peak_mb, t.frames,
       t.error_trace, t.nsys_report, s.run_dir,
       coalesce(t.event, 'no_terminal_event') AS terminal_event,
       t.error_stage, t.timing_mode, s.build_id, s.symbol
FROM s LEFT JOIN t USING (run_id);

-- Formal home for anomalies. Append-only; resolution is a later defect_events table, never an UPDATE.
CREATE TABLE defects (
    defect_id   VARCHAR PRIMARY KEY,            -- <yyyymmdd>_<kernel_id|scope>_<kind>
    ts          TIMESTAMP NOT NULL DEFAULT now(),
    kernel_id   VARCHAR,                        -- NULL for environment-scope defects
    run_id      VARCHAR,                        -- NULL when found by static inspection
    build_id    VARCHAR,
    kind        VARCHAR NOT NULL,               -- banned_runtime_abi | alloc_thrash | unchecked_cuda_call | stub_merge | missing_source |
                                                -- binary_name_mismatch | missing_symbol | internal_stream | low_gpu_share | cpu_pixel_touch | toolchain_path
    severity    VARCHAR NOT NULL CHECK (severity IN ('blocker','high','medium','low')),
    blocks_runner BOOLEAN NOT NULL DEFAULT false,
    detail      VARCHAR NOT NULL,
    evidence    VARCHAR,                        -- exact command + output fragment
    source      VARCHAR NOT NULL DEFAULT 'agent_check'   -- agent_check | operator | runner
);

CREATE VIEW v_open_blockers AS
SELECT d.kernel_id, d.kind, d.severity, d.detail
FROM defects d WHERE d.blocks_runner;

CREATE VIEW v_run_defects AS
SELECT r.run_id, r.kernel_id, r.terminal_event, d.kind, d.severity, d.detail
FROM runs r JOIN defects d USING (run_id);

-- ---------- seed: findings from 2026-10-03 backfill (sql/020) ----------
INSERT INTO defects (defect_id, ts, kernel_id, kind, severity, blocks_runner, detail, evidence) VALUES
('20261003_screen_kernel_banned_runtime_abi', TIMESTAMP '2026-10-03 09:36:13', 'screen_kernel', 'banned_runtime_abi', 'blocker', true,
 'Blocked by runtime architecture. Only binary is an ATen/c10/caffe2 extension .pyd; screen_kernel.cu has no dllexport. No shim or loader will be written. Unblock = extern "C" port.',
 'dumpbin /exports screen_agent_cuda.cp311-win_amd64.pyd -> 78 exports: c10/caffe2 C++ symbols + PyInit_screen_agent_cuda'),
('20261003_object_clear_banned_runtime_abi', TIMESTAMP '2026-10-03 09:36:13', 'object_clear', 'banned_runtime_abi', 'blocker', true,
 'Blocked by runtime architecture. Only binary is an ATen/c10/caffe2 extension .pyd (two copies: object_clear_cuda\ and build\lib.win-amd64-cpython-311\object_clear_cuda\). No shim or loader will be written.',
 'dumpbin /exports object_clear_cuda_cpp.cp311-win_amd64.pyd -> 78 exports: c10/caffe2 C++ symbols + PyInit_object_clear_cuda_cpp'),
('20261003_diff_embed_kernel_banned_runtime_abi', TIMESTAMP '2026-10-03 09:36:13', 'diff_embed_kernel', 'banned_runtime_abi', 'blocker', true,
 'Blocked by runtime architecture. ATen extension header + PYBIND11_MODULE. Superseded by diff_embed_kernel_tc. No shim or loader will be written.',
 'dumpbin /exports diff_embed_cuda.cp311-win_amd64.pyd -> c10/caffe2 symbols + PyInit_diff_embed_cuda; git diff shows ATen extension include + TORCH_CHECK macros'),
('20261003_diff_embed_kernel_tc_alloc_thrash', TIMESTAMP '2026-10-03 09:36:48', 'diff_embed_kernel_tc', 'alloc_thrash', 'high', false,
 'cu_batch_cosine_similarity: when any of queries/targets/out_scores is a host pointer, does cudaMalloc + cudaFree for that buffer on every call. Needs device-pointer ingestion (caller-owned or cached buffers) before production benchmarking.',
 'git diff --no-index diff_embed_cuda vs turbo-cuda-duckdb csrc/diff_embed_kernel.cu: cudaMalloc((void**)&d_q_alloc, q_bytes) ... if (d_q_alloc) cudaFree(d_q_alloc);'),
('20261003_diff_embed_kernel_tc_unchecked_cuda_call', TIMESTAMP '2026-10-03 09:36:48', 'diff_embed_kernel_tc', 'unchecked_cuda_call', 'high', false,
 'cudaMemcpyAsync H2D (x2) and D2H return values ignored; cudaStreamSynchronize/cudaDeviceSynchronize return ignored; launch error only surfaced via trailing cudaGetLastError. Needs checked stream calls before production benchmarking.',
 'cudaMemcpyAsync(d_q_alloc, queries, q_bytes, cudaMemcpyHostToDevice, stream);  (no status check)'),
('20261003_cu_geopin_solver_stub_merge', TIMESTAMP '2026-10-03 09:36:13', 'cu_geopin_solver', 'stub_merge', 'low', false,
 'cu_geopin_init and cu_bowling_init resolve to the same RVA in cu_vision_lite_sm89.dll (identical-code folding). cu_geopin_init body is cudaFree(0); return 0; so behaviour is equivalent, but per-symbol profiling cannot tell them apart.',
 'dumpbin /exports cu_vision_lite_sm89.dll: cu_bowling_init 00003A70, cu_geopin_init 00003A70'),
('20261003_cu_dense_stereo_missing_source', TIMESTAMP '2026-10-03 09:37:13', 'cu_dense_stereo', 'missing_source', 'medium', false,
 'cu_marching_cubes is exported by cu_vision_lite_sm89.dll but no registered csrc file declares it. sm89 was built from sources not in the registry.',
 'git grep --no-index CUDA_EXPORT|dllexport c:\dev\cu_vision_lite\csrc -> no cu_marching_cubes'),
('20261003_arrow_sq8_search_binary_name_mismatch', TIMESTAMP '2026-10-03 09:36:13', 'arrow_sq8_search', 'binary_name_mismatch', 'low', false,
 'c:\dev\turbo-cuda-duckdb\turbo_cuda_duckdb\turbo_cuda.dll has internal export-table name turbo_cuda_v2.dll and an identical export list; it is a renamed copy of turbo_cuda_v2.dll. Applies to every turbo_cuda kernel.',
 'dumpbin /exports turbo_cuda.dll -> "Section contains the following exports for turbo_cuda_v2.dll"'),
('20261003_adaptive_delta_fused_internal_stream', TIMESTAMP '2026-10-03 09:41:11', 'adaptive_delta_fused', 'internal_stream', 'medium', false,
 'Entrypoints take no cudaStream_t; module creates its own static g_stream (cudaStreamNonBlocking). Host cudaEvents on its own stream will not bracket the work; runner must use timing_mode=internal_stream (device-sync bracketing) until a stream parameter is added. Also writes h_out_bitmask to a host pointer.',
 'screen_agent_cuda/csrc/adaptive_delta_fused.cu:121 cudaStreamCreateWithFlags(&g_stream, cudaStreamNonBlocking); :156 uint32_t* h_out_bitmask'),
('20261003_env_toolchain_path', TIMESTAMP '2026-10-03 09:36:39', NULL, 'toolchain_path', 'medium', false,
 'nvcc.exe and dumpbin.exe are not on PATH for workspace_exec_array. Resolved by absolute path: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin\nvcc.exe, C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\dumpbin.exe.',
 'spawn nvcc.exe ENOENT (exit -4058); spawn dumpbin.exe ENOENT (exit -4058)');

COMMIT;
