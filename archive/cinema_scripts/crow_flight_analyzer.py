"""
crow_flight_analyzer.py
======================
Analyzes B:\\crows.MOV to find exact timestamps, bounding boxes, and flight paths
of crows across the entire video.
"""

import os
import sys
import json
import subprocess
import numpy as np

FFMPEG = "ffmpeg.exe"
FFPROBE = "ffprobe.exe"
DEV_PATH = r"C:\dev"
if DEV_PATH not in sys.path:
    sys.path.insert(0, DEV_PATH)

import cu_vision_lite
from cu_vision_lite import cu_track_ball_gpu

def analyze_crows(video_path=r"B:\crows.MOV"):
    probe_cmd = [
        FFPROBE, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,nb_frames,r_frame_rate",
        "-of", "json", video_path
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    info = json.loads(res.stdout)["streams"][0]
    w = int(info["width"])
    h = int(info["height"])
    nb_frames = int(info.get("nb_frames", 573))
    
    ds = 4
    ds_w = w // ds
    ds_h = h // ds
    sky_h = int(ds_h * 0.50)
    
    dec_cmd = [
        FFMPEG, "-hwaccel", "cuda", "-i", video_path,
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
    ]
    pipe = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    raw_size = w * h * 3
    prev_ds_gray = None
    detections = []
    
    for f in range(nb_frames):
        data = pipe.stdout.read(raw_size)
        if len(data) < raw_size:
            break
        frame = np.frombuffer(data, dtype=np.uint8).reshape((h, w, 3))
        ds_frame = frame[::ds, ::ds]
        ds_gray = ((ds_frame[:, :, 0].astype(np.int32) * 77 + 
                    ds_frame[:, :, 1].astype(np.int32) * 150 + 
                    ds_frame[:, :, 2].astype(np.int32) * 29) >> 8).astype(np.uint8)
                    
        # Check sky for dark pixels
        sky = ds_gray[:sky_h, :]
        dark = np.argwhere(sky < 95)
        
        det = None
        if prev_ds_gray is not None:
            res_gpu = cu_track_ball_gpu(ds_gray, prev_ds_gray, roi=(0, 0, ds_w, sky_h), threshold=12)
            if res_gpu is not None:
                cx, cy, count = res_gpu
                if 5 <= count <= 1500:
                    det = {"frame": f, "x": cx * ds, "y": cy * ds, "count": count, "type": "motion"}
                    
        if det is None and 4 <= len(dark) <= 800:
            det = {"frame": f, "x": int(np.median(dark[:, 1]) * ds), "y": int(np.median(dark[:, 0]) * ds), "count": len(dark), "type": "dark"}
            
        if det:
            detections.append(det)
        prev_ds_gray = ds_gray
        
    pipe.stdout.close()
    pipe.wait()
    
    print(f"Total detections: {len(detections)} / {nb_frames} frames")
    # Group detections into continuous segments
    segments = []
    current_seg = []
    for d in detections:
        if not current_seg or d["frame"] - current_seg[-1]["frame"] <= 8:
            current_seg.append(d)
        else:
            if len(current_seg) >= 12:
                segments.append(current_seg)
            current_seg = [d]
    if len(current_seg) >= 12:
        segments.append(current_seg)
        
    print(f"\nDiscovered {len(segments)} valid flight passes:")
    for i, seg in enumerate(segments):
        start_f = seg[0]["frame"]
        end_f = seg[-1]["frame"]
        dur = (end_f - start_f) / 24.0
        x_span = abs(seg[-1]["x"] - seg[0]["x"])
        print(f"  Pass {i+1}: Frames {start_f}..{end_f} (t={start_f/24:.2f}s..{end_f/24:.2f}s, dur={dur:.2f}s) | Travel: {x_span}px")
        
    return segments

if __name__ == "__main__":
    analyze_crows()
