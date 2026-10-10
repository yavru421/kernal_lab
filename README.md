# kernel_lab

A bare-metal test bench and empirical ledger for custom CUDA kernels running on an RTX 4060 (AD107 / SM_89, Windows).

Most GPU codebases devolve into unversioned notebooks, loose test scripts, and benchmark numbers that hide regressions. When you rebuild a kernel or change a warp shuffle, did it actually get faster? Did tracking drift worsen? Did an unnoticed host-side CPU copy sneak into the wrapper?

In this repo, **every single kernel run is treated as an audited laboratory experiment**. No run counts as completed until its wall clock, GPU execution time, peak VRAM, input hash, and human verdict are written to an embedded DuckDB ledger (`kernel_lab.duckdb`).

---

## 1. The Core Architecture

- **Bare-Metal Host (`host/`)**: A native C++ binary (`kernel_host.exe`) that dynamically loads C-ABI DLLs (`cu_vision_lite.dll`, `cu_skeleton_kinematics.dll`, `screen_agent_cuda.dll`). No container layers, no hidden CPU memcpy fallbacks.
- **Embedded Ledger (`kernel_lab.duckdb`)**: An append-only DuckDB database recording kernel builds, hardware metrics, run manifests, output SHA-256 hashes, and operator verdicts.
- **Immutable Run Folders (`runs/<run_id>/`)**: Every execution writes its manifest, telemetry JSON, and contact sheets to an isolated run directory. Video outputs are kept off git; manifests and metrics are committed.

---

## 2. Real Hardware Benchmarks (Queried from the Ledger)

Real numbers across 87 benchmarked runs on the RTX 4060 Laptop GPU (SM_89, 8 GB VRAM):

| Kernel / Tool | Runs | Mean GPU Time | Mean Wall Time | Primary Task |
|---|---|---|---|---|
| `cu_video_face_tracker` | 19 | 87.1 ms / frame | 48.5 s (full clip) | 106-pt dense facial tracking + 6-DoF PnP |
| `cu_guided_matting` | 16 | 1,451.2 ms | 2,055.1 ms | Alpha matte extraction from skeleton trimaps |
| `cu_skeleton_kinematics` | 13 | 31.3 s | 89.6 s | 17-keypoint biomechanics & joint moments |
| `cu_puppet_engine` | 13 | 1,687.2 ms | 1,687.3 ms | 2D character mesh deformation driving Blender |
| `cu_geopin_solver` | 7 | 48.3 s | 48.7 s | Multi-point sub-pixel patch tracking (Levenberg-Marquardt) |
| `adaptive_delta_fused` | 3 | 415.6 ms | 773.0 ms | Macroblock visual difference detection |

### Honest Human Evaluation
The `verdicts` table records operator inspection results directly against run IDs:
- **Good / Great**: 46 runs
- **Pass**: 2 runs
- **Garbage**: 9 runs (preserved with exact error traces and tracking loss logs, rather than scrubbed from history)

---

## 3. Production Pipelines in this Repo

### A. Dual-Worker Concrete Demolition Kinematics (`scripts/multi_subject_tracker.py`)
Built for continuous jobsite footage where standard computer vision models fail due to heavy dust, vibration, and extreme occlusions:
- **Chromatic Invariant Re-ID**: Separates two workers by high-vis shirt color (safety orange vs neon yellow) instead of running heavy, slow neural Re-ID backbones.
- **Spatial Tripwire State Machine**: Automatically counts concrete removal cycles by detecting transitions between physical zones (`X > 520` trench pry $\rightarrow$ `X < 450` trailer bed toss).
- **Biomechanical Load Estimation**: Evaluates 17-keypoint skeleton joint angles to estimate knee flexion, lumbar strain, and L5/S1 spinal moments across carry weights (20 kg single carry, 35 kg pry, 0 kg return).

### B. Clavicle-Anchored Cranium Tracking (`scripts/animate_2d_face_rig.py`)
Standard face trackers lose lock when a subject turns $>60^\circ$ away from the camera:
- Combines 17 COCO body keypoints with 106 dense facial landmarks.
- Uses the subject's **clavicles and sternum** as a geometric prior anchor to stabilize bounding boxes through a 2D Kalman filter.
- Computes 6-DoF head pose (pitch, yaw, roll) via Levenberg-Marquardt PnP and drives dynamic 2D cartoon puppet deformation meshes in Blender with zero manual keyframing.

---

## 4. Querying the Ledger

Inspect the database directly with the native DuckDB CLI:

```bash
# View kernel usage breakdown
duckdb kernel_lab.duckdb "SELECT * FROM v_kernel_usage ORDER BY runs DESC;"

# View recent runs with operator verdicts
duckdb kernel_lab.duckdb "SELECT run_id, kernel_id, gpu_ms, verdict, note FROM v_run_latest_verdict ORDER BY ts_start DESC LIMIT 15;"
```

---

## 5. Running the Host

The native C++ runner (`host/bin/kernel_host.exe`) runs without any Python layer:

```cmd
# Execute a kernel run
kernel_host.exe --kernel cu_geopin_solver --input clip.mov --caller john --subject bowling

# Record an operator verdict against a run
kernel_host.exe --verdict good --run 20261003T142843_cu_geopin_solver_001 --note "solid track"
```
