"""
crow_hero_cutter.py
===================
Autonomous Avian Centering, Dead-Frame Pruning & Optical Slow-Mo Pipeline.
Filters out every frame without birds, centers telephoto camera on flying crows,
and renders butter-smooth slow-motion via AD107 NVENC acceleration.
"""

import os
import sys
import time
import subprocess
import numpy as np
from PIL import Image

DEV_PATH = r"C:\dev"
if DEV_PATH not in sys.path:
    sys.path.insert(0, DEV_PATH)

import cu_vision_lite
from cu_vision_lite import cu_track_ball_gpu

FFMPEG = "ffmpeg.exe"
FFPROBE = "ffprobe.exe"
MIND_DUCKDB_PATH = r"C:\Users\John\.gemini\config\mind.duckdb"

def analyze_and_cut_crows(
    input_video: str = r"B:\crows_cuda_stabilized.mp4",
    output_video: str = r"B:\crows_slowmo_centered.mp4",
    zoom_factor: float = 3.5,
    slowdown_factor: float = 2.0, # 50% slow-mo (2x duration)
    output_fps: int = 60,
    dark_thresh: int = 115,
    min_pixels: int = 8,
    max_pixels: int = 4000,
    downsample: int = 4
):
    print("=" * 80)
    print("[CROW HERO CUTTER] Zero-Dead-Frame Avian Centered Slow-Mo Engine")
    print(f"  -> Input Video:      {input_video}")
    print(f"  -> Output Video:     {output_video}")
    print(f"  -> Zoom Factor:      {zoom_factor:.1f}x")
    print(f"  -> Slowdown Factor:  {slowdown_factor:.1f}x")
    print(f"  -> Target FPS:       {output_fps} FPS")
    print("=" * 80)

    if not os.path.exists(input_video):
        print(f"[FAIL-FAST ERROR] Video not found: {input_video}")
        sys.exit(1)

    # 1. Probe input video
    probe_cmd = [
        FFPROBE, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,nb_frames,r_frame_rate,duration",
        "-of", "json", input_video
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    import json
    info = json.loads(res.stdout)["streams"][0]
    in_w = int(info["width"])
    in_h = int(info["height"])
    fps_parts = info.get("r_frame_rate", "24/1").split("/")
    in_fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 24.0
    nb_frames = int(info.get("nb_frames", 573))

    out_w, out_h = 1920, 1080
    crop_w = int(in_w / zoom_factor)
    crop_h = int(in_h / zoom_factor)
    half_crop_w = crop_w // 2
    half_crop_h = crop_h // 2

    ds_w = in_w // downsample
    ds_h = in_h // downsample
    sky_h = int(ds_h * 0.58) # Sky boundary strictly excluding lower trees

    print(f"  -> Input Stream:     {in_w}x{in_h} @ {in_fps:.2f} FPS ({nb_frames} frames)")
    print(f"  -> Telephoto Window: {crop_w}x{crop_h} -> {out_w}x{out_h}")
    print(f"  -> Sky Search Space: [0, 0, {ds_w}, {sky_h}]")

    # --------------------------------------------------------------------------
    # PASS 1: Frame-by-Frame Avian Detection & Coordinate Extraction
    # --------------------------------------------------------------------------
    print("\n=== [PASS 1] Scanning Frames for Airborne Avian Presence ===")
    dec_cmd = [
        FFMPEG, "-hwaccel", "cuda", "-i", input_video,
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
    ]
    pipe_in = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    raw_frame_size = in_w * in_h * 3

    frame_detections = []
    prev_ds_gray = None
    frame_idx = 0
    t0 = time.time()

    # Try importing scipy label
    try:
        from scipy.ndimage import label, center_of_mass
        has_scipy = True
    except ImportError:
        has_scipy = False

    while True:
        raw_bytes = pipe_in.stdout.read(raw_frame_size)
        if len(raw_bytes) < raw_frame_size:
            break

        frame = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((in_h, in_w, 3))
        ds_frame = frame[::downsample, ::downsample]
        ds_gray = ((ds_frame[:, :, 0].astype(np.int32) * 77 + 
                    ds_frame[:, :, 1].astype(np.int32) * 150 + 
                    ds_frame[:, :, 2].astype(np.int32) * 29) >> 8).astype(np.uint8)

        detected = False
        target_x = None
        target_y = None
        bird_mass = 0

        # Method A: AD107 CUDA Differential Motion Kernel
        if prev_ds_gray is not None:
            roi = (0, 0, ds_w, sky_h)
            res = cu_track_ball_gpu(ds_gray, prev_ds_gray, roi=roi, threshold=12)
            if res is not None:
                cx, cy, count = res
                if min_pixels <= count <= max_pixels:
                    target_x = float(cx * downsample)
                    target_y = float(cy * downsample)
                    bird_mass = count
                    detected = True

        # Method B: Direct Dark-Blob Clustering in Sky ROI (handles gliding/stationary silhouette)
        if not detected:
            sky_gray = ds_gray[:sky_h, :]
            dark_mask = sky_gray < dark_thresh
            dark_count = np.count_nonzero(dark_mask)

            if min_pixels <= dark_count <= max_pixels:
                if has_scipy:
                    labeled, num_features = label(dark_mask)
                    if num_features > 0:
                        # Find largest cluster
                        sizes = np.bincount(labeled.ravel())[1:]
                        if len(sizes) > 0 and sizes.max() >= min_pixels:
                            best_label = np.argmax(sizes) + 1
                            cy_ds, cx_ds = center_of_mass(labeled == best_label)
                            target_x = float(cx_ds * downsample)
                            target_y = float(cy_ds * downsample)
                            bird_mass = sizes.max()
                            detected = True
                else:
                    # Pure numpy median centroid
                    ys, xs = np.nonzero(dark_mask)
                    if len(xs) >= min_pixels:
                        target_x = float(np.median(xs) * downsample)
                        target_y = float(np.median(ys) * downsample)
                        bird_mass = len(xs)
                        detected = True

        prev_ds_gray = ds_gray
        frame_detections.append({
            "frame_idx": frame_idx,
            "detected": detected,
            "x": target_x,
            "y": target_y,
            "mass": bird_mass
        })
        frame_idx += 1

        if frame_idx % 100 == 0 or frame_idx == nb_frames:
            n_det = sum(1 for d in frame_detections if d["detected"])
            print(f"  Scanned {frame_idx:3d}/{nb_frames} frames | Detected birds in {n_det} frames")

    pipe_in.stdout.close()
    pipe_in.wait()

    # --------------------------------------------------------------------------
    # PASS 2: Temporal Filtering & Gap Bridging (Prune Dead Frames)
    # --------------------------------------------------------------------------
    print("\n=== [PASS 2] Pruning Dead Frames & Smoothing Camera Trajectory ===")
    
    # Bridge small detection dropouts (<= 3 frames)
    for i in range(1, len(frame_detections) - 1):
        if not frame_detections[i]["detected"]:
            prev_d = frame_detections[i - 1]
            if prev_d["detected"] and prev_d["x"] is not None:
                for k in range(1, 4):
                    if i + k < len(frame_detections) and frame_detections[i + k]["detected"] and frame_detections[i + k]["x"] is not None:
                        next_d = frame_detections[i + k]
                        frac = 1.0 / (k + 1)
                        frame_detections[i]["detected"] = True
                        frame_detections[i]["x"] = prev_d["x"] * (1 - frac) + next_d["x"] * frac
                        frame_detections[i]["y"] = prev_d["y"] * (1 - frac) + next_d["y"] * frac
                        break

    # Extract ONLY frames that have birds
    valid_indices = [d["frame_idx"] for d in frame_detections if d["detected"]]
    print(f"  -> Total source frames:      {nb_frames}")
    print(f"  -> Frames with active birds: {len(valid_indices)} ({len(valid_indices)/nb_frames*100:.1f}%)")
    print(f"  -> Pruned dead frames:       {nb_frames - len(valid_indices)} (Cut away)")

    if len(valid_indices) == 0:
        print("[FAIL-FAST ERROR] No bird frames detected! Aborting.")
        sys.exit(1)

    # Smooth camera coordinates across the valid bird sequence
    smooth_coords = {}
    cur_x = frame_detections[valid_indices[0]]["x"]
    cur_y = frame_detections[valid_indices[0]]["y"]
    alpha = 0.18 # Camera glide damping

    for f_idx in valid_indices:
        det = frame_detections[f_idx]
        cur_x = alpha * det["x"] + (1.0 - alpha) * cur_x
        cur_y = alpha * det["y"] + (1.0 - alpha) * cur_y

        # Clamp camera to valid sky bounds
        max_allowed_y = int(in_h * 0.58)
        safe_cx = max(half_crop_w, min(in_w - half_crop_w, int(cur_x)))
        safe_cy = max(half_crop_h, min(max_allowed_y, int(cur_y)))
        smooth_coords[f_idx] = (safe_cx, safe_cy)

    # --------------------------------------------------------------------------
    # PASS 3: Extract Centered Crops & Render 60 FPS Optical Slow-Mo
    # --------------------------------------------------------------------------
    print("\n=== [PASS 3] Extracting Centered Crops & Rendering Slow-Mo Reel ===")
    
    # Setup decode pipe (re-reading input video)
    dec_cmd2 = [
        FFMPEG, "-hwaccel", "cuda", "-i", input_video,
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
    ]
    pipe_in2 = subprocess.Popen(dec_cmd2, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    # Setup hardware NVENC encoder pipe
    # Slowdown: repeat each valid frame `repeats` times to achieve smooth slow motion at 60 FPS
    repeats = int(round(slowdown_factor * (output_fps / in_fps)))
    total_out_frames = len(valid_indices) * repeats

    enc_cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{out_w}x{out_h}", "-r", f"{output_fps}",
        "-i", "-",
        "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
        "-pix_fmt", "yuv420p",
        output_video
    ]
    pipe_out = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    valid_set = set(valid_indices)
    curr_frame_idx = 0
    written_frames = 0
    t_render0 = time.time()

    try:
        while True:
            raw_bytes = pipe_in2.stdout.read(raw_frame_size)
            if len(raw_bytes) < raw_frame_size:
                break

            if curr_frame_idx in valid_set:
                frame = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((in_h, in_w, 3))
                cx, cy = smooth_coords[curr_frame_idx]

                y0 = cy - half_crop_h
                y1 = y0 + crop_h
                x0 = cx - half_crop_w
                x1 = x0 + crop_w

                crop_np = frame[y0:y1, x0:x1]
                crop_img = Image.fromarray(crop_np)
                out_img = crop_img.resize((out_w, out_h), resample=Image.BICUBIC)
                out_bytes = out_img.tobytes()

                # Duplicate frame to stretch time smoothly
                for _ in range(repeats):
                    pipe_out.stdin.write(out_bytes)
                    written_frames += 1

                if curr_frame_idx % 25 == 0 or curr_frame_idx == valid_indices[-1]:
                    print(f"  Centered Frame {curr_frame_idx:3d} | Pos: ({cx:4d}, {cy:4d}) | Written: {written_frames:4d}/{total_out_frames}")

            curr_frame_idx += 1

    finally:
        pipe_in2.stdout.close()
        pipe_out.stdin.close()
        pipe_in2.wait()
        pipe_out.wait()

    dur_out = written_frames / output_fps
    elapsed = time.time() - t_render0
    print(f"\n[OK] Centered Avian Slow-Mo Reel Complete: {output_video}")
    print(f"  -> Total Output Frames: {written_frames} ({dur_out:.2f}s @ {output_fps} FPS)")
    print(f"  -> Render Latency:      {elapsed:.2f}s ({written_frames/elapsed:.1f} FPS)")

    # 4. Generate 4x4 proof sheet
    contact_jpg = output_video.replace(".mp4", "_contact.jpg")
    step = max(1, written_frames // 16)
    contact_cmd = [
        FFMPEG, "-y", "-i", output_video,
        "-vf", f"select='not(mod(n,{step}))',scale=480:270,tile=4x4",
        "-frames:v", "1", "-update", "1", contact_jpg
    ]
    subprocess.run(contact_cmd, check=True)
    print(f"[OK] Verification Proof Sheet: {contact_jpg}")

    # 5. Persist milestone to DuckDB
    try:
        import duckdb
        con = duckdb.connect(MIND_DUCKDB_PATH)
        event_id = f"VID_CROWS_HERO_CUT_{int(time.time())}"
        norm_path = output_video.replace("\\", "/")
        con.execute("""
            INSERT OR REPLACE INTO mind.main.video_events (event_id, video_path, timestamp_sec, event_type, scene_score, logged_at)
            VALUES (?, ?, ?, 'crow_hero_cutter_complete', 1.0, CURRENT_TIMESTAMP);
        """, [event_id, norm_path, dur_out])
        con.close()
        print(f"[OK] Telemetry persisted to mind.duckdb: {event_id}")
    except Exception as e:
        print(f"[WARN] DuckDB log error: {e}")

    return output_video

if __name__ == "__main__":
    analyze_and_cut_crows()
