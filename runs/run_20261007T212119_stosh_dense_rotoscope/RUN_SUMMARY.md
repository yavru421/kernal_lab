# Run Summary: cu_dense_rotoscope (660 Frames)

- **Run ID**: `run_20261007T212119_stosh_dense_rotoscope`
- **Kernel ID**: `cu_dense_rotoscope` (SM_89 Architecture)
- **Source Video**: `B:\stosh\stosh_point_brewery\stosh_brewery_order_strongest_beer.mp4`
  - Resolution: 1080 x 1920 (Vertical 9:16)
  - Duration: 22.0 seconds (660 frames @ 30 FPS)
  - Input SHA256: `93aff5d1c16494503236eb83b43e27c1b69f0a379bac6aabb366cf5097342bba`
- **Telemetry Source**: `C:\dev\kernel_lab\runs\run_20261007T140500_brewery_skeleton_face_tracker\outputs\face_tracks.json`
  - 106 facial landmarks per frame
  - 17 COCO skeletal keypoints per frame
  - 1€ Adaptive Filter: `min_cutoff = 2.5 Hz`, `beta = 0.03`

## Hardware & Kernel Performance
- **Target Hardware**: NVIDIA GeForce RTX 4060 Laptop GPU (AD107, 8188 MiB, Driver 616.92)
- **CUDA Architecture**: `sm_89` (Ada Lovelace)
- **Total Frames Processed**: 660
- **Total GPU Kernel Time**: 6,265.51 ms (9.493 ms / frame)
- **Total Wall Time**: 6,265.48 ms (6.27 s)
- **Throughput**: 105.3 FPS (3.5x real-time @ 30 FPS)
- **VRAM Utilization**: 1,513 MiB / 8,188 MiB (stable, zero leak)

## Vector Rotoscope Topology
1. **Facial Contours (106 Landmark Sub-Pixel Loops)**:
   - Jawline perimeter (Points 0–32, cyan core `#00e6ff` with dark ink perimeter)
   - Left & Right Eyebrow Arches (Points 33–52, amber gold `#ffb400`)
   - Nasal Bridge & Wing Contours (Points 53–71, cyan `#00d2ff`)
   - Eye Orbits & Eyelid Perimeters (Points 72–87, neon yellow `#ffe600`)
   - Outer & Inner Lip Margins (Points 88–103, neon crimson `#ff1e64`)
   - Left & Right Pupil Focal Nodes (Points 104, 105, luminous cyan `#00c8ff`)
   - Nasolabial & Philtrum Cross-Links (61/71 -> 88/92, columella 65 -> upper lip 88/90)
2. **Kinematic Skeletal Structure (17 COCO Keypoints)**:
   - Bi-acromial Clavicle Girdle (Joints 5–6)
   - Upper & Forearm Bones (5->7->9 left, 6->8->10 right, neon emerald `#00ff96`)
   - Concentric Joint Articulation Nodes (Shoulders, Elbows, Wrists)
   - Thoracic / Lumbar Spine & Lateral Flanks (Anchored to hip joints 11–12)
   - Cervical Neck Connector: Dynamically bonded to Chin Landmark 16 when face is active, Nose KP 0 in profile
3. **Anatomical Body-Anchor Gating**:
   - Suppresses 200px fallback bounding box hallucination in frames 0–40 when Stosh looks down in profile.
   - Smoothly transitions into full 106-point facial vector contours as head rotates toward camera.

## Deliverable Artifacts
- **Final Deliverable MP4 (Original Audio Muxed)**:
  `C:\dev\kernel_lab\runs\run_20261007T212119_stosh_dense_rotoscope\outputs\stosh_dense_rotoscope_with_audio_660f.mp4`
  (Size: 43,460,684 bytes, SHA256: `f3d49d649fdea5ff6e2070d05805dd95468d2c06f74a9367f017f44efba110ad`)
- **Side-by-Side Comparison MP4**:
  `C:\dev\kernel_lab\runs\run_20261007T212119_stosh_dense_rotoscope\outputs\stosh_dense_rotoscope_side_by_side_660f.mp4`
  (Size: 181,894,684 bytes, SHA256: `bfb403b134a7d2c23dcb84096116991639b3debea8c2a66ee5639e2aef3c69e2`)
- **Deliverable 4x4 Contact Sheet**:
  `C:\dev\kernel_lab\runs\run_20261007T212119_stosh_dense_rotoscope\outputs\stosh_dense_rotoscope_contact_sheet.png`
  (Size: 3,202,774 bytes, SHA256: `badc50fc0e874ff5f9ef60c2ce7f9e0dbd742d1243845aa47ddc40ad4a6a235b`)
