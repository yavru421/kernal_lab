-- Usage and health views. Time-window by caller; no blind LIMITs.

CREATE OR REPLACE VIEW v_kernel_usage AS
SELECT k.kernel_id, k.repo, k.category, k.status,
       count(r.run_id)                        AS runs,
       count(*) FILTER (WHERE r.ok)           AS ok_runs,
       min(r.ts_start)                        AS first_run,
       max(r.ts_start)                        AS last_run,
       avg(r.gpu_ms)                          AS avg_gpu_ms,
       max(r.vram_peak_mb)                    AS max_vram_mb
FROM kernels k LEFT JOIN runs r USING (kernel_id)
GROUP BY ALL;

CREATE OR REPLACE VIEW v_verdict_rate AS
SELECT r.kernel_id, r.subject, v.verdict, count(*) AS n
FROM runs r JOIN verdicts v USING (run_id)
GROUP BY ALL;

-- Kernels with a source but no DLL and no successful build.
CREATE OR REPLACE VIEW v_unbuilt AS
SELECT k.kernel_id, k.repo, k.source_path
FROM kernels k
WHERE k.dll_path IS NULL
  AND NOT EXISTS (SELECT 1 FROM builds b WHERE b.kernel_id = k.kernel_id AND b.ok);

-- Kernels never exercised in the ledger.
CREATE OR REPLACE VIEW v_never_run AS
SELECT k.kernel_id, k.repo, k.category
FROM kernels k
WHERE NOT EXISTS (SELECT 1 FROM runs r WHERE r.kernel_id = k.kernel_id);

-- Latest verdict per run (verdicts can be revised).
CREATE OR REPLACE VIEW v_run_latest_verdict AS
SELECT r.run_id, r.kernel_id, r.subject, r.ok, r.gpu_ms,
       arg_max(v.verdict, v.ts) AS verdict
FROM runs r LEFT JOIN verdicts v USING (run_id)
GROUP BY ALL;
