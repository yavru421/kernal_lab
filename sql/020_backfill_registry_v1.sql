-- 020_backfill_registry_v1.sql  (2026-10-03)
-- Source evidence:
--   DLL discovery : Everything HTTP (port 7999) via workspace_search_everything
--   Exports       : dumpbin.exe /exports (MSVC 14.44.35207 Hostx64\x64) via workspace_exec_array
--   Ownership     : git grep --no-index on CUDA_EXPORT / dllexport in each csrc
--   Duplicates    : git diff --no-index (byte/line), not the embedding diff tool
-- "ATen/c10 extension" below = .pyd whose export table is c10/caffe2 C++ symbols + PyInit_* only (no C-ABI). Logged as a defect.
BEGIN TRANSACTION;

-- ---------- cu_vision_lite (monolith cu_vision_lite_sm89.dll, 23 exports) ----------
UPDATE kernels SET dll_path='c:\dev\cu_vision_lite\cu_vision_lite_sm89.dll',
  exports='cu_vision_init,cu_vision_transform,cu_histogram_diagnostics', status='builds'
  WHERE kernel_id='cu_vision_lite';
UPDATE kernels SET dll_path='c:\dev\cu_vision_lite\cu_vision_lite_sm89.dll',
  exports='cu_bowling_init,cu_bowling_track_ball,cu_bowling_eval_pindeck', status='builds'
  WHERE kernel_id='cu_bowling_tracker';
UPDATE kernels SET dll_path='c:\dev\cu_vision_lite\cu_vision_lite_sm89.dll',
  exports='cu_dxgi_init,cu_dxgi_acquire_frame_to_device,cu_dxgi_get_dimensions,cu_dxgi_release', status='builds'
  WHERE kernel_id='cu_dxgi_capture';
UPDATE kernels SET dll_path='c:\dev\cu_vision_lite\cu_vision_lite_sm89.dll',
  exports='cu_features_init,cu_sobel_edge,cu_morphology,cu_template_match', status='builds'
  WHERE kernel_id='cu_vision_features';
UPDATE kernels SET dll_path='c:\dev\cu_vision_lite\cu_vision_lite_sm89.dll',
  exports='cu_mask_dilate_21x21,cu_gaussian_feather_9x9', status='builds'
  WHERE kernel_id='cu_object_clear_ops';
UPDATE kernels SET dll_path='c:\dev\cu_vision_lite\cu_vision_lite_sm89.dll',
  exports='cu_geopin_init,cu_geopin_extract_patches,cu_geopin_track_step,cu_geopin_bidirectional_solve_pair', status='builds',
  notes='CANONICAL. git diff --no-index vs c:\dev\cuda_pin_tracker\csrc\cu_geopin_solver.cu: exit 0, zero lines differ (byte-identical). Kept canonical here because it ships inside cu_vision_lite_sm89.dll which callers already load. DEFECT: cu_geopin_init and cu_bowling_init share RVA 0x3A70 in sm89 (linker identical-code folding; verify both are trivial stubs).'
  WHERE kernel_id='cu_geopin_solver';
UPDATE kernels SET dll_path='c:\dev\cu_vision_lite\cu_dense_stereo.dll',
  exports='cu_plane_sweep_stereo,cu_tsdf_integrate,cu_backproject_pointcloud,cu_extract_tsdf_surface', status='builds',
  notes='cu_vision_lite_sm89.dll also exports cu_plane_sweep_stereo, cu_tsdf_integrate and cu_marching_cubes; cu_marching_cubes has no CUDA_EXPORT in any registered csrc file (source unknown).'
  WHERE kernel_id='cu_dense_stereo';
UPDATE kernels SET exports='cu_solve_kinematic_telemetry,cu_solve_kinematic_telemetry_device', status='builds'
  WHERE kernel_id='cu_skeleton_kinematics';

UPDATE kernels SET dll_path='c:\dev\cuda_pin_tracker\cu_geopin_solver.dll',
  exports='cu_geopin_init,cu_geopin_extract_patches,cu_geopin_track_step,cu_geopin_bidirectional_solve_pair', status='builds',
  notes='DUPLICATE of cu_geopin_solver (byte-identical source, git diff --no-index exit 0). Not canonical. Retire candidate once callers are confirmed.'
  WHERE kernel_id='cu_geopin_solver_pt';

-- ---------- screen_agent_cuda ----------
UPDATE kernels SET dll_path='c:\dev\screen_agent_cuda\screen_agent_cuda_v2.dll',
  exports='cu_init_screen_engine,cu_adaptive_delta_fused,cu_eval_stalled_cadence,cu_get_internal_rgb_chw_ptr', status='builds',
  notes='Also in screen_agent_cuda.dll (v1, same 4 + NvOptimusEnablementCuda). v2 chosen: superset.'
  WHERE kernel_id='adaptive_delta_fused';
UPDATE kernels SET dll_path='c:\dev\screen_agent_cuda\screen_agent_cuda_v2.dll',
  exports='cu_dxgi_ocr_tensor_init,cu_process_dxgi_surface', status='builds'
  WHERE kernel_id='dxgi_ocr_tensor';
UPDATE kernels SET dll_path='c:\dev\screen_agent_cuda\screen_agent_cuda.cp311-win_amd64.pyd',
  exports='PyInit_screen_agent_cuda', status='builds',
  notes='DEFECT: no C-ABI. screen_kernel.cu has no dllexport; only binary is an ATen/c10 extension .pyd. Banned runtime path. Needs extern "C" port before the runner can load it.'
  WHERE kernel_id='screen_kernel';

-- ---------- turbo-cuda-duckdb (turbo_cuda_v2.dll; turbo_cuda_duckdb\turbo_cuda.dll has identical export table and internal name turbo_cuda_v2.dll) ----------
UPDATE kernels SET dll_path='c:\dev\turbo-cuda-duckdb\turbo_cuda_v2.dll',
  exports='cu_arrow_sq8_search,cu_arrow_sq8_search_cached,cache_int8_matrix_named,cu_enable_l2_persistence_cached,cu_set_l2_persistence_window', status='builds'
  WHERE kernel_id='arrow_sq8_search';
UPDATE kernels SET dll_path='c:\dev\turbo-cuda-duckdb\turbo_cuda_v2.dll',
  exports='cu_init_intent_patterns,cu_resolve_intent_topk', status='builds'
  WHERE kernel_id='intent_telepathy';
UPDATE kernels SET dll_path='c:\dev\turbo-cuda-duckdb\turbo_cuda_v2.dll',
  exports='cu_eval_neuromotor_clc,cu_eval_lacquaniti_power_law', status='builds'
  WHERE kernel_id='neuromotor_clc';
UPDATE kernels SET dll_path='c:\dev\turbo-cuda-duckdb\turbo_cuda_v2.dll',
  exports='cache_vram_matrix,cache_vram_matrix_named,free_vram_matrix_cache,free_vram_matrix_cache_named,run_cuda_cached_dot_product,run_cuda_cached_dot_product_named,run_cuda_cosine_similarity,run_cuda_cosine_similarity_ext', status='builds'
  WHERE kernel_id='vector_ops';
UPDATE kernels SET dll_path='c:\dev\turbo-cuda-duckdb\turbo_cuda_v2.dll',
  exports='cu_batch_cosine_similarity', status='builds',
  notes='CANONICAL diff_embed kernel. git diff --no-index vs diff_embed_cuda copy: 95 insertions, 41 deletions. This copy: pure extern "C" cu_batch_cosine_similarity, 2D grid (queries x targets), stream arg, host/device pointer auto-detect, error codes -1..-4. Other copy is an ATen extension + PYBIND11 1D query-vs-db kernel (banned path). DEFECT: host-pointer path does cudaMalloc/cudaFree per call and ignores cudaMemcpyAsync return codes.'
  WHERE kernel_id='diff_embed_kernel_tc';
UPDATE kernels SET dll_path='c:\dev\diff_embed_cuda\diff_embed_cuda.cp311-win_amd64.pyd',
  exports='PyInit_diff_embed_cuda', status='builds',
  notes='NOT CANONICAL. Superseded by diff_embed_kernel_tc (turbo-cuda-duckdb). ATen/c10 extension (PYBIND11_MODULE). Backs workspace_cuda_diff, which is an AST/embedding diff, NOT a frame diff. Retire candidate.'
  WHERE kernel_id='diff_embed_kernel';

-- ---------- speech-mcp-server (kokoro_mel_bridge_v2.dll superset of v1) ----------
UPDATE kernels SET dll_path='c:\dev\speech-mcp-server\kokoro_mel_bridge_v2.dll',
  exports='cu_init_mel_bridge,cu_compute_mel_spectrogram,cu_get_mel_output_device_ptr', status='builds',
  notes='Also in kokoro_mel_bridge.dll (v1, same 3). v2 chosen: superset.'
  WHERE kernel_id='kokoro_mel_bridge';
UPDATE kernels SET dll_path='c:\dev\speech-mcp-server\kokoro_mel_bridge_v2.dll',
  exports='cu_init_audio_vad,cu_process_mic_chunk', status='builds'
  WHERE kernel_id='audio_vad_gate';

-- ---------- CGMusicalComposition ----------
UPDATE kernels SET dll_path='c:\dev\CGMusicalComposition\band_dsp_cuda.dll',
  exports='cu_binaural_pola_init,cu_binaural_pola_destroy,cu_binaural_pola_process_block,cu_binaural_pola_process_stream,cu_binaural_pola_generate_hall_acoustics,cu_benchmark_pola_latency,cu_get_device_telemetry', status='builds'
  WHERE kernel_id='band_dsp_cuda';

-- ---------- vram_swap_cuda ----------
UPDATE kernels SET dll_path='c:\dev\vram_swap_cuda\vram_swap_cuda.dll',
  exports='vram_swap_init,vram_swap_shutdown,vram_swap_alloc_blocks,vram_swap_free_blocks,vram_swap_get_pinned_ptr,vram_swap_get_stats,vram_swap_gpu_checksum,vram_swap_gpu_generate,vram_swap_read_pinned,vram_swap_write_pinned,vram_swap_sync', status='builds'
  WHERE kernel_id='vram_swap_kernel';
UPDATE kernels SET dll_path='c:\dev\vram_swap_cuda\continuous_stream_daemon.dll',
  exports='daemon_init,daemon_tick,daemon_shutdown,daemon_get_frame_count,daemon_get_stream_ms', status='builds'
  WHERE kernel_id='continuous_stream_daemon';
UPDATE kernels SET dll_path='c:\dev\vram_swap_cuda\native_audio_kernel.dll',
  exports='cu_synthesize_voice_gpu,cu_apply_reverb_gpu,cu_watchdog_set_cpu_limit,cu_watchdog_check_and_abort', status='builds'
  WHERE kernel_id='native_audio_kernel';
UPDATE kernels SET dll_path='c:\dev\vram_swap_cuda\turbo_vector_kernel.dll',
  exports='cu_turbo_int8_scan,cu_turbo_int8_batch_scan', status='builds'
  WHERE kernel_id='turbo_vector_kernel';
UPDATE kernels SET dll_path='c:\dev\vram_swap_cuda\unified_offload_engine.dll',
  exports='cu_ast_parallel_grep,cu_direct_screen_delta,cu_duckdb_vector_scan', status='builds'
  WHERE kernel_id='unified_offload_engine';

-- ---------- faceswap_engine / object_clear_cuda ----------
UPDATE kernels SET dll_path='c:\dev\faceswap_engine\faceswap_engine_cuda.dll',
  exports='cu_fused_affine_warp_preprocess,cu_fused_mask_morphology,cu_fused_reinhard_color_transfer,cu_parallel_jacobi_poisson_blend', status='builds'
  WHERE kernel_id='faceswap_kernels';
UPDATE kernels SET dll_path='c:\dev\object_clear_cuda\object_clear_cuda\object_clear_cuda_cpp.cp311-win_amd64.pyd',
  exports='PyInit_object_clear_cuda_cpp', status='builds',
  notes='DEFECT: no C-ABI. Only binary is an ATen/c10 extension .pyd. Duplicate copy at build\lib.win-amd64-cpython-311\object_clear_cuda\. Banned runtime path.'
  WHERE kernel_id='object_clear';

-- ---------- not built ----------
UPDATE kernels SET notes='No built binary found in Everything index (searched ext:dll;pyd under c:\dev\dxgi-cuda-frame-delta). Source declares extern "C" RunFrameDeltaExtraction. Candidate real frame-diff kernel for footage work.'
  WHERE kernel_id='dxgi_cuda_delta';
UPDATE kernels SET notes='No built binary found in Everything index (searched ext:dll;pyd under c:\dev\pdf_preview_cuda). Header defines PDF_CUDA_API dllexport.'
  WHERE kernel_id='pdf_preview_cuda';

-- ---------- first builds row: toolchain baseline (no rebuild: no build script exists in c:\dev\cu_vision_lite) ----------
INSERT INTO builds (build_id, kernel_id, ts, nvcc_version, arch, flags, dll_path, dll_sha256, ok, log_path, error_trace)
VALUES ('20261003T093654_cu_vision_lite_baseline', 'cu_vision_lite', TIMESTAMP '2026-10-03 09:36:54',
  'Cuda compilation tools, release 12.6, V12.6.85 (Build cuda_12.6.r12.6/compiler.35059454_0) at C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin\nvcc.exe',
  'sm_89',
  'BASELINE ONLY, no rebuild. GPU: NVIDIA GeForce RTX 4060 Laptop GPU, driver 616.92, 8188 MiB total, 1568 MiB used, 46C, 0% util, compute_cap 8.9',
  'c:\dev\cu_vision_lite\cu_vision_lite_sm89.dll',
  '7a422d5cf99bed37c81cfa2b3ad9490849973997a1ef46167fe42be93428f8fa',
  NULL, NULL,
  'No build script in c:\dev\cu_vision_lite (Everything: build*.bat|build*.ps1|build*.cmd|CMakeLists.txt|Makefile|setup.py -> 0 results); flags of existing DLL unknown. Toolchain not on PATH: "spawn nvcc.exe ENOENT" (exit -4058), "spawn dumpbin.exe ENOENT" (exit -4058); resolved by absolute path.');

COMMIT;
