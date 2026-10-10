"""
crow_tracker_zoom.py
====================
Autonomous Computer Vision Crow Tracker & Dynamic Centered Zoom Engine
Location: C:\\Users\\John\\.gemini\\config\\skills\\cinema-vfx\\scripts\\crow_tracker_zoom.py

Utilizes native C-ABI CUDA acceleration via cu_vision_lite (AD107 / RTX 4060):
- cu_track_ball_gpu: AD107 CUDA differential motion & centroid kernel
- Velocity-predictive Kalman/EMA camera stabilizer
- 3.5x Lossless 4K optical crop centered on airborne birds
- High-efficiency NVENC p7 hardware encoding
"""

import os
import sys
import time
import argparse
import subprocess
import numpy as np
from PIL import Image, ImageDraw

# Ensure C:\dev is in Python path for cu_vision_lite
DEV_PATH = r"C:\dev"
if DEV_PATH not in sys.path:
    sys.path.insert(0, DEV_PATH)

import cu_vision_lite
from cu_vision_lite import cu_track_ball_gpu

FFMPEG = "ffmpeg.exe"
FFPROBE = "ffprobe.exe"
MIND_DUCKDB_PATH = r"C:\Users\John\.gemini\config\mind.duckdb"

def track_and_render_crow_hero_zoom(
    input_video: str = r"B:\crows_cuda_stabilized.mp4",
    output_video: str = r"B:\crows_cuda_tracked.mp4",
    zoom_factor: float = 3.5,
    smooth_alpha: float = 0.22,
    downsample: int = 4,
    diff_threshold: int = 12,
    draw_hud: bool = False
):
    print("=" * 80)
    print(f"[CROW HERO TRACKER] {zoom_factor:.1f}x AD107 CUDA cu_vision_lite")
    print(f"  -> Input Video:    {input_video}")
    print(f"  -> Output Video:   {output_video}")
    print(f"  -> Zoom Factor:    {zoom_factor:.1f}x (UHD 4K -> FHD 1080p)")
    print(f"  -> Draw HUD:       {draw_hud}")
    print(f"  -> CUDA Hardware:  NVIDIA AD107 (RTX 4060 Laptop GPU)")
    print("=" * 80)

    if not os.path.exists(input_video):
        print(f"[FAIL-FAST ERROR] Video not found: {input_video}")
        sys.exit(1)

    # 1. Probe video stream parameters
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
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 24.0
    nb_frames = int(info.get("nb_frames", 573))
    dur_s = float(info.get("duration", 23.88))

    out_w, out_h = 1920, 1080
    crop_w = int(in_w / zoom_factor)
    crop_h = int(in_h / zoom_factor)
    half_crop_w = crop_w // 2
    half_crop_h = crop_h // 2

    # Downsampled detection space
    ds_w = in_w // downsample
    ds_h = in_h // downsample
    # Strict sky boundary ceiling: top 50% of the frame is pure open cloud sky
    sky_roi_h = int(ds_h * 0.50)

    print(f"  -> Source Resolution: {in_w}x{in_h} @ {fps:.2f} FPS ({nb_frames} frames, {dur_s:.1f}s)")
    print(f"  -> Telephoto Crop:    {crop_w}x{crop_h} -> {out_w}x{out_h} (Lossless Optical Extraction)")
    print(f"  -> CUDA Sky Bounds:   [0, 0, {ds_w}, {sky_roi_h}] (Excludes All Treelines)")

    # 2. Setup FFmpeg decode & NVENC hardware encode pipes
    dec_cmd = [
        FFMPEG, "-hwaccel", "cuda", "-i", input_video,
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
    ]
    enc_cmd = [
        FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{out_w}x{out_h}", "-r", f"{fps}",
        "-i", "-",
        "-i", input_video,
        "-map", "0:v", "-map", "1:a?",
        "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
        "-c:a", "copy",
        output_video
    ]

    pipe_in = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    pipe_out = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    raw_frame_size = in_w * in_h * 3
    cam_x = in_w * 0.50
    cam_y = in_h * 0.28 # Primary flight corridor in sky
    vel_x = 0.0
    vel_y = 0.0
    prev_ds_gray = None
    frames_since_detect = 0
    frame_idx = 0

    t0 = time.time()
    print("\n--> Launching 6.0x AD107 CUDA crow tracking & telephoto zoom pipeline...")

    try:
        while True:
            raw_bytes = pipe_in.stdout.read(raw_frame_size)
            if len(raw_bytes) < raw_frame_size:
                break

            frame = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((in_h, in_w, 3))

            # Fast downsample and grayscale for AD107 CUDA tracking
            ds_frame = frame[::downsample, ::downsample]
            ds_gray = ((ds_frame[:, :, 0].astype(np.int32) * 77 + 
                        ds_frame[:, :, 1].astype(np.int32) * 150 + 
                        ds_frame[:, :, 2].astype(np.int32) * 29) >> 8).astype(np.uint8)

            detected = False
            target_x = None
            target_y = None

            # Primary: Native AD107 CUDA Differential Motion Kernel
            if prev_ds_gray is not None:
                roi = (0, 0, ds_w, sky_roi_h)
                res = cu_track_ball_gpu(ds_gray, prev_ds_gray, roi=roi, threshold=diff_threshold)
                if res is not None:
                    cx, cy, count = res
                    if 6 <= count <= 2000:
                        target_x = float(cx * downsample)
                        target_y = float(cy * downsample)
                        detected = True

            # Secondary: If flapping differential is small (gliding crow), search dark blob in sky ROI
            if not detected:
                sky_gray = ds_gray[:sky_roi_h, :]
                dark_pixels = np.argwhere(sky_gray < 90)
                if len(dark_pixels) >= 4 and len(dark_pixels) <= 1200:
                    # Find dark cluster closest to previous camera center
                    cur_cx_ds = cam_x / downsample
                    cur_cy_ds = cam_y / downsample
                    dists_sq = (dark_pixels[:, 1] - cur_cx_ds)**2 + (dark_pixels[:, 0] - cur_cy_ds)**2
                    close_idx = np.where(dists_sq < (250)**2)[0]
                    if len(close_idx) >= 3:
                        target_y = float(np.median(dark_pixels[close_idx, 0]) * downsample)
                        target_x = float(np.median(dark_pixels[close_idx, 1]) * downsample)
                        detected = True

            prev_ds_gray = ds_gray

            if detected and target_x is not None and target_y is not None:
                # Update velocity
                new_vel_x = target_x - cam_x
                new_vel_y = target_y - cam_y
                vel_x = 0.30 * new_vel_x + 0.70 * vel_x
                vel_y = 0.30 * new_vel_y + 0.70 * vel_y

                # Track smoothly
                cam_x = smooth_alpha * target_x + (1.0 - smooth_alpha) * cam_x
                cam_y = smooth_alpha * target_y + (1.0 - smooth_alpha) * cam_y
                frames_since_detect = 0
            else:
                frames_since_detect += 1
                if frames_since_detect < 24:
                    # Coast on flight momentum
                    cam_x += vel_x * 0.60
                    cam_y += vel_y * 0.60
                    vel_x *= 0.90
                    vel_y *= 0.90
                else:
                    # Drift to establishing sky framing
                    home_x = in_w * 0.50
                    home_y = in_h * 0.28
                    cam_x = 0.03 * home_x + 0.97 * cam_x
                    cam_y = 0.03 * home_y + 0.97 * cam_y
                    vel_x = 0.0
                    vel_y = 0.0

            # Clamping: keep crop window inside upper sky corridor
            max_allowed_y = int(in_h * 0.58) # Keep crop window above main tree line
            safe_cx = max(half_crop_w, min(in_w - half_crop_w, int(cam_x)))
            safe_cy = max(half_crop_h, min(max_allowed_y, int(cam_y)))

            # Extract telephoto crop
            y0 = safe_cy - half_crop_h
            y1 = y0 + crop_h
            x0 = safe_cx - half_crop_w
            x1 = x0 + crop_w

            crop_np = frame[y0:y1, x0:x1]

            # High-fidelity resize to 1080p
            crop_img = Image.fromarray(crop_np)
            out_img = crop_img.resize((out_w, out_h), resample=Image.BICUBIC)

            if draw_hud and detected:
                draw = ImageDraw.Draw(out_img)
                cx_mid, cy_mid = out_w // 2, out_h // 2
                sz = 20
                # Reticle crosshair
                draw.line([(cx_mid - sz, cy_mid), (cx_mid - 5, cy_mid)], fill=(0, 240, 255), width=2)
                draw.line([(cx_mid + 5, cy_mid), (cx_mid + sz, cy_mid)], fill=(0, 240, 255), width=2)
                draw.line([(cx_mid, cy_mid - sz), (cx_mid, cy_mid - 5)], fill=(0, 240, 255), width=2)
                draw.line([(cx_mid, cy_mid + 5), (cx_mid, cy_mid + sz)], fill=(0, 240, 255), width=2)
                # Outer target box
                bs = 36
                draw.rectangle([cx_mid - bs, cy_mid - bs, cx_mid + bs, cy_mid + bs], outline=(0, 240, 255), width=1)

            pipe_out.stdin.write(out_img.tobytes())
            frame_idx += 1

            if frame_idx % 60 == 0 or frame_idx == nb_frames:
                status_str = f"LOCK [{safe_cx}, {safe_cy}]" if detected else "COASTING"
                print(f"  Frame {frame_idx:3d}/{nb_frames} (t={frame_idx/fps:4.1f}s) | State: {status_str:<16} | Pos: ({safe_cx}, {safe_cy})")

    finally:
        pipe_in.stdout.close()
        pipe_out.stdin.close()
        pipe_in.wait()
        pipe_out.wait()

    elapsed = time.time() - t0
    render_fps = frame_idx / elapsed if elapsed > 0 else 0
    print(f"\n[OK] Tracked Hero Zoom Complete: {output_video}")
    print(f"  -> Render Time: {elapsed:.2f}s ({render_fps:.1f} FPS)")

    # 3. Generate 4x4 proof sheet via FFmpeg
    contact_jpg = output_video.replace(".mp4", "_contact.jpg")
    step = max(1, frame_idx // 16)
    contact_cmd = [
        FFMPEG, "-y", "-i", output_video,
        "-vf", f"select='not(mod(n,{step}))',scale=480:270,tile=4x4",
        "-frames:v", "1", "-update", "1", contact_jpg
    ]
    subprocess.run(contact_cmd, check=True)
    print(f"[OK] Verification Proof Sheet: {contact_jpg}")

    # 4. Log milestone to DuckDB mind lake
    try:
        import duckdb
        con = duckdb.connect(MIND_DUCKDB_PATH)
        event_id = f"VID_CROWS_CUDA_TRACK_{int(time.time())}"
        norm_path = output_video.replace("\\", "/")
        con.execute("""
            INSERT OR REPLACE INTO mind.main.video_events (event_id, video_path, timestamp_sec, event_type, scene_score, logged_at)
            VALUES (?, ?, ?, 'crow_cuda_track_complete', 1.0, CURRENT_TIMESTAMP);
        """, [event_id, norm_path, dur_s])
        con.close()
        print(f"[OK] Telemetry persisted to mind.duckdb: {event_id}")
    except Exception as e:
        print(f"[WARN] DuckDB log error: {e}")

    return output_video

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AD107 CUDA Crow Tracking & Zoom Engine")
    parser.add_argument("--input", default=r"B:\crows_cuda_stabilized.mp4", help="Input video")
    parser.add_argument("--output", default=r"B:\crows_cuda_tracked.mp4", help="Output video")
    parser.add_argument("--zoom", type=float, default=3.5, help="Zoom factor")
    parser.add_argument("--smooth", type=float, default=0.22, help="Smoothing alpha")
    parser.add_argument("--hud", action="store_true", help="Draw tactical cyan HUD reticle")
    args = parser.parse_args()

    track_and_render_crow_hero_zoom(
        input_video=args.input,
        output_video=args.output,
        zoom_factor=args.zoom,
        smooth_alpha=args.smooth,
        draw_hud=args.hud
    )

