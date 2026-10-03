-- 040_seed_golden_inputs_v1.sql
-- Seed authoritative golden inputs for continuous video CUDA benchmark suites.

INSERT OR REPLACE INTO golden_inputs (golden_id, kernel_id, input_path, input_sha256, expectation, registered_at)
VALUES 
  (
    'golden_cu_geopin_bowling_v1',
    'cu_geopin_solver',
    'C:\Users\John\Downloads\prahl_outings\bowling.MOV',
    '11b87abb95eeb80975d1e320f8fca3ab2c646035d57545257889d6584a1876fb',
    'Lane landmark pins remain locked (confidence >= 0.85, status=1) across continuous 1080x1920 frame sequence without spatial drift',
    now()
  ),
  (
    'golden_cu_geopin_backup_v1',
    'cu_geopin_solver',
    'C:\Users\John\Downloads\backup.MOV',
    '834c651511acbc4d8c13b0338fa02fa6f5ba2365b37352372d2d6f9294f0a03f',
    'Biomechanical landmark tracking on approach with continuous lock and forward-backward consistency',
    now()
  );
