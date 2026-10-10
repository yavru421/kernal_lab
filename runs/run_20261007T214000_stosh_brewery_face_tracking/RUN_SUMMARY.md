# Run Summary: /face_tracking (`cu_video_face_tracker`)

- **Run ID**: `run_20261007T214000_stosh_brewery_face_tracking`
- **Kernel / Tool ID**: `cu_video_face_tracker`
- **Source Video**: `B:\stosh\stosh_point_brewery\stosh_brewery_order_strongest_beer.mp4`
  - Resolution: 1080 x 1920 (Vertical 9:16)
  - Duration: 22.0 seconds (660 frames @ 30.0 FPS)
  - Input SHA256: `93aff5d1c16494503236eb83b43e27c1b69f0a379bac6aabb366cf5097342bba`

## Hardware & Tracking Performance
- **Target Hardware**: NVIDIA GeForce RTX 4060 Laptop GPU (AD107, 8188 MiB, Driver 616.92)
- **Total Frames**: 660
- **Mean Frame Latency**: 88.63 ms (11.3 FPS throughput)
- **Total Wall Duration**: 67.28 seconds
- **Models**:
  - `yolov8n-pose.onnx`: 17 COCO Keypoints for Clavicle & Cranium Anchor
  - `2d106det.onnx`: 106 Dense Facial Landmarks on 192x192 Cropped ROI
  - 2D Kalman Filter Box Stabilization & 6-DoF Levenberg-Marquardt PnP Head Pose

## DuckDB Telemetry Auditing (`kernel_lab.duckdb`)
### Prior Source Breakdown
- `pure_facial_kps`: 454 frames (68.79%, avg confidence 0.71, avg RMSE 1.15)
- `fallback_frame_center`: 191 frames (28.94%)
- `facial_kps_blend`: 9 frames (1.36%, avg confidence 0.52)
- `skeleton_clavicle`: 6 frames (0.91%, avg confidence 0.49)

### 6-DoF Head Pose Range
- **Pitch**: 25.1° to 51.8° (head tilt looking down vs looking up)
- **Yaw**: 9.5° to 90.0° (near-frontal to extreme 90° profile)
- **Roll**: -58.0° to 34.2°

## Deliverables Generated
1. **Broadcast Tracked Video with Audio**:
   `C:\dev\kernel_lab\runs\run_20261007T214000_stosh_brewery_face_tracking\outputs\tracked_face_with_audio.mp4`
   (42,403,911 bytes, SHA256: `17f14d649bf86d4334a560b60a45d2f7942030c7aa1fb748228d1251beee3f71`)
2. **Isolated Black Background Video with Audio**:
   `C:\dev\kernel_lab\runs\run_20261007T214000_stosh_brewery_face_tracking\outputs\tracked_face_isolated_with_audio.mp4`
   (9,132,794 bytes, SHA256: `dfacca555343ed2a43796654b2b9f2c9b2d15c7f2de3951c5f0609bb0b8b71d2`)
3. **Side-by-Side Comparison Video**:
   `C:\dev\kernel_lab\runs\run_20261007T214000_stosh_brewery_face_tracking\outputs\tracked_face_side_by_side.mp4`
   (181,633,818 bytes, SHA256: `081289fed31b374ec50b85d591cd8f3dec6114f978d2f9f34c1ab51e541c975b`)
4. **4x4 Broadcast Contact Sheet**:
   `C:\dev\kernel_lab\runs\run_20261007T214000_stosh_brewery_face_tracking\outputs\tracked_face_contact_sheet.png`
   (3,124,868 bytes, SHA256: `fd3e894952582f14e4155a46d6e9142ebf416fab1c3326ea73a77dfdfdfda98f`)
5. **4x4 Isolated Contact Sheet**:
   `C:\dev\kernel_lab\runs\run_20261007T214000_stosh_brewery_face_tracking\outputs\tracked_face_isolated_contact_sheet.png`
   (116,508 bytes, SHA256: `1f3ef4efb4ac4684872c624230f24a729b61d9822ef11c8fe595c7cf6207f9a4`)
6. **Trajectory Telemetry**:
   `C:\dev\kernel_lab\runs\run_20261007T214000_stosh_brewery_face_tracking\outputs\face_tracks.json`
   (1,960,393 bytes)
