-- 050_log_skeleton_run.sql
-- Immutable ledger registration for cu_skeleton_kinematics golden run on bowling.MOV

INSERT OR REPLACE INTO golden_inputs (golden_id, kernel_id, input_path, input_sha256, expectation, registered_at)
VALUES (
    'golden_cu_skeleton_bowling_v1',
    'cu_skeleton_kinematics',
    'C:\Users\John\Downloads\prahl_outings\bowling.MOV',
    '11b87abb95eeb80975d1e320f8fca3ab2c646035d57545257889d6584a1876fb',
    '17-joint COCO biomechanical skeleton tracking across 519 frames with mean CUDA kernel latency < 1.0 ms and valid joint confidence >= 0.80',
    now()
);

INSERT INTO run_events (
    event_id, run_id, event, kernel_id, dll_path, dll_sha256, symbol, adapter_sha256,
    caller, subject, input_path, params_json, golden_id, run_dir, host_version, gpu_state_pre
) VALUES (
    '20261003T112720_cu_skeleton_kinematics_001:started',
    '20261003T112720_cu_skeleton_kinematics_001',
    'started',
    'cu_skeleton_kinematics',
    'c:\dev\cu_vision_lite\cu_vision_lite_sm89.dll',
    '7a422d5cf99bed37c81cfa2b3ad9490849973997a1ef46167fe42be93428f8fa',
    'cu_solve_kinematic_telemetry',
    '79b32c66804a9d701dfdbe4da4cbf239f1ff4fdfa0531c36fe9f60f69f21f7db',
    'operator_eval',
    'bowling_biomechanical_skeleton',
    'C:\Users\John\Downloads\prahl_outings\bowling.MOV',
    '{"load_mass_kg": 7.26}',
    'golden_cu_skeleton_bowling_v1',
    'c:\dev\kernel_lab\runs\20261003T112720_cu_skeleton_kinematics_001',
    'kernel_host/0.3.2',
    'NVIDIA GeForce RTX 4060 Laptop GPU, 616.92, 8188 MiB, 2180 MiB, 50, 0 %, 8.9'
);

INSERT INTO run_events (
    event_id, run_id, event, ok, gpu_ms, wall_ms, vram_peak_mb, frames, timing_mode,
    error_stage, error_trace, gpu_state_post
) VALUES (
    '20261003T112720_cu_skeleton_kinematics_001:finished',
    '20261003T112720_cu_skeleton_kinematics_001',
    'finished',
    true,
    499.85,
    22970.0,
    270.0,
    519,
    'host_stream',
    '',
    '',
    'NVIDIA GeForce RTX 4060 Laptop GPU, 616.92, 8188 MiB, 2450 MiB, 53, 98 %, 8.9'
);

INSERT OR REPLACE INTO outputs (output_id, run_id, path, kind, bytes, sha256) VALUES
(
    '20261003T112720_cu_skeleton_kinematics_001_video',
    '20261003T112720_cu_skeleton_kinematics_001',
    'outputs/tracked_skeleton.mp4',
    'video',
    9998081,
    'fb2a72dabf7f6493b4fdf45b0436545c49e523e55f4717364f657c3c58ac750f'
),
(
    '20261003T112720_cu_skeleton_kinematics_001_summary',
    '20261003T112720_cu_skeleton_kinematics_001',
    'outputs/kinematics_summary.json',
    'telemetry_json',
    1408,
    '46867211718c78bf0da3abdb0f51ee29a2fcd7d44a3a067c21f99225078d6737'
),
(
    '20261003T112720_cu_skeleton_kinematics_001_preview',
    '20261003T112720_cu_skeleton_kinematics_001',
    'outputs/preview_f120.jpg',
    'image',
    72973,
    '0cf77583ac64cae93ef7ba43a67dae93c7698000700ccd37a0ffa0a267b1afa7'
);
