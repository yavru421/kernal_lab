-- kernel_lab ledger schema v1
-- Every kernel invocation, build and operator verdict is recorded here.
-- Append-only by convention: never UPDATE/DELETE runs; add a verdict row instead.

CREATE TABLE IF NOT EXISTS kernels (
    kernel_id      VARCHAR PRIMARY KEY,   -- stable slug, e.g. 'cu_geopin_solver'
    repo           VARCHAR NOT NULL,      -- owning repo under c:\dev
    source_path    VARCHAR NOT NULL,      -- .cu source (reference, not a copy)
    dll_path       VARCHAR,               -- built C-ABI DLL that exports it, if any
    category       VARCHAR,               -- vision | tracking | pose | stereo | diff | capture | audio | vector | db | misc
    exports        VARCHAR,               -- comma list of exported C symbols (fill as verified)
    status         VARCHAR DEFAULT 'unverified', -- unverified | builds | runs | validated | retired
    notes          VARCHAR,
    registered_at  TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS builds (
    build_id       VARCHAR PRIMARY KEY,
    kernel_id      VARCHAR NOT NULL,
    ts             TIMESTAMP DEFAULT now(),
    nvcc_version   VARCHAR,
    arch           VARCHAR,               -- e.g. sm_89
    flags          VARCHAR,
    dll_path       VARCHAR,
    dll_sha256     VARCHAR,
    ok             BOOLEAN,
    log_path       VARCHAR,
    error_trace    VARCHAR
);

CREATE TABLE IF NOT EXISTS runs (
    run_id         VARCHAR PRIMARY KEY,   -- yyyymmddThhmmss_<kernel>_<seq>
    ts_start       TIMESTAMP DEFAULT now(),
    ts_end         TIMESTAMP,
    kernel_id      VARCHAR NOT NULL,
    caller         VARCHAR,               -- project/skill/tool that invoked it (cu_vision_lite, cinema-vfx, ...)
    subject        VARCHAR,               -- what it was pointed at: bowling, concrete_float, crows, ...
    input_path     VARCHAR,
    input_sha256   VARCHAR,
    params_json    VARCHAR,
    ok             BOOLEAN,
    gpu_ms         DOUBLE,
    wall_ms        DOUBLE,
    vram_peak_mb   DOUBLE,
    frames         BIGINT,
    error_trace    VARCHAR,               -- exact trace, never summarized
    nsys_report    VARCHAR,
    run_dir        VARCHAR                -- c:\dev\kernel_lab\runs\<run_id>\
);

CREATE TABLE IF NOT EXISTS outputs (
    output_id      VARCHAR PRIMARY KEY,
    run_id         VARCHAR NOT NULL,
    path           VARCHAR NOT NULL,
    kind           VARCHAR,               -- video | telemetry_json | frames | mesh | image | log
    bytes          BIGINT,
    sha256         VARCHAR
);

-- Operator judgment lives apart from the run so it can be added or revised later.
CREATE TABLE IF NOT EXISTS verdicts (
    verdict_id     VARCHAR PRIMARY KEY,
    run_id         VARCHAR NOT NULL,
    ts             TIMESTAMP DEFAULT now(),
    verdict        VARCHAR NOT NULL,      -- great | good | meh | garbage | wrong_tool
    note           VARCHAR,
    source         VARCHAR DEFAULT 'operator'  -- operator | agent_check
);

-- Golden clips: fixed inputs used to compare a kernel across builds.
CREATE TABLE IF NOT EXISTS golden_inputs (
    golden_id      VARCHAR PRIMARY KEY,
    kernel_id      VARCHAR NOT NULL,
    input_path     VARCHAR NOT NULL,
    input_sha256   VARCHAR,
    expectation    VARCHAR,               -- plain-English pass condition
    registered_at  TIMESTAMP DEFAULT now()
);
