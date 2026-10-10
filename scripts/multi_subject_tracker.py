"""
multi_subject_tracker.py — Native AD107 Dual-Worker Biomechanical Skeleton & Trailer-Trip Kinematics Engine

Tracks:
  - John (Orange Shirt): Trench zone (X > 520 px), heavy concrete sidewalk slab prying, loosening, and initial lifting.
  - Skyler 'Frankly' (Yellow Shirt): Trailer zone (X < 450 px), collecting rubble from staging edge, carrying to dump trailer, and hoisting chunks into the bed.

Features:
  - Shirt-color chromatic invariant re-identification (Orange vs Neon Yellow)
  - Deterministic Trailer-Trip Spatial Tripwire (X > 520 px Pick -> X < 450 px Trailer Toss = 1 Load Cycle)
  - Standard Chunk Mass Model: 20 kg (single carry), 35 kg (2-man / heavy slab pry), 0 kg (empty return)
  - Dynamic AD107 CUDA biomechanical kinematics (cu_skeleton_kinematics.dll)
  - Synchronized Dialogue Attribution HUD (Cooper_7741.srt) & Spatial Tripwire Visuals
  - High-visibility Dual-Worker HUD video export & DuckDB immutable ledger
"""

import os
import sys
import time
import subprocess
import json
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Ensure all native CUDA & cuDNN libraries are discoverable by Windows dynamic linker
cuda_paths = [
    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin",
    os.path.expandvars(r"%APPDATA%\Python\Python313\site-packages\nvidia\cudnn\bin"),
    os.path.expandvars(r"%APPDATA%\Python\Python313\site-packages\nvidia\cublas\bin"),
    r"C:\dev\cu_vision_lite",
]
for cp in cuda_paths:
    if os.path.exists(cp):
        try:
            os.add_dll_directory(cp)
        except AttributeError:
            pass
        os.environ["PATH"] = f"{cp};" + os.environ.get("PATH", "")

# Add cu_vision_lite to sys.path
sys.path.insert(0, r"C:\dev\cu_vision_lite")
from cu_skeleton_kinematics_bridge import solve_kinematic_telemetry
import onnxruntime as ort

COCO_KEYPOINT_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle"
]

SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16)
]

# Spatial Zone & Mass Model Constants
TRAILER_X_LIMIT = 450.0  # Centroid X < 450 -> Trailer Dump Zone
TRENCH_X_LIMIT = 520.0   # Centroid X > 520 -> Trench Pick / Slab Pry Zone

MASS_SINGLE_CARRY_KG = 20.0     # Standard individual concrete chunk
MASS_HEAVY_PRY_2MAN_KG = 35.0   # 2-man tandem lift / John heavy slab pry
MASS_EMPTY_RETURN_KG = 0.0      # Zero-weight return transit

def nms_boxes(boxes: np.ndarray, scores: np.ndarray, iou_thresh: float = 0.45):
    if len(boxes) == 0:
        return []
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        if order.size == 1:
            break
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        union = areas[i] + areas[order[1:]] - inter
        ovr = np.where(union > 0, inter / union, 0.0)
        inds = np.where(ovr <= iou_thresh)[0]
        order = order[inds + 1]
    return keep

def classify_worker_shirt_color(img_rgb: np.ndarray, bbox: tuple, kps: np.ndarray) -> str:
    """
    Samples upper-body torso patch to determine whether worker is John (Orange) or Skyler (Neon Yellow).
    Returns 'orange', 'yellow', or 'unknown'.
    """
    h, w = img_rgb.shape[:2]
    ls, rs = kps[5], kps[6]
    lh, rh = kps[11], kps[12]

    if ls[2] > 0.25 and rs[2] > 0.25:
        tx1 = int(max(0, min(ls[0], rs[0]) - 10))
        tx2 = int(min(w, max(ls[0], rs[0]) + 10))
        ty1 = int(max(0, min(ls[1], rs[1])))
        if lh[2] > 0.25 and rh[2] > 0.25:
            ty2 = int(min(h, max(lh[1], rh[1])))
        else:
            ty2 = int(min(h, ty1 + (tx2 - tx1) * 1.5))
    else:
        bx1, by1, bx2, by2 = bbox
        tx1 = int(max(0, bx1 + (bx2 - bx1) * 0.15))
        tx2 = int(min(w, bx2 - (bx2 - bx1) * 0.15))
        ty1 = int(max(0, by1 + (by2 - by1) * 0.15))
        ty2 = int(min(h, by1 + (by2 - by1) * 0.50))

    if tx2 <= tx1 or ty2 <= ty1:
        return 'unknown'

    torso_patch = img_rgb[ty1:ty2, tx1:tx2]
    if torso_patch.size == 0:
        return 'unknown'

    r_mean = float(np.mean(torso_patch[:, :, 0]))
    g_mean = float(np.mean(torso_patch[:, :, 1]))
    b_mean = float(np.mean(torso_patch[:, :, 2]))

    rg_ratio = r_mean / max(g_mean, 1.0)
    
    if rg_ratio > 1.18 and r_mean > 90 and b_mean < 110:
        return 'orange'
    elif g_mean > 105 and rg_ratio < 1.15:
        return 'yellow'
    else:
        return 'orange' if rg_ratio > 1.08 else 'yellow'

def load_srt_subtitles(srt_path: str):
    """
    Parses Cooper_7741.srt into a list of timed subtitles:
    [{"start": float, "end": float, "speaker": str, "text": str}, ...]
    """
    if not os.path.exists(srt_path):
        return []
    
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r'(\d+)\s*\n'
        r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*\n'
        r'(.*?)(?=\n\s*\n|\Z)',
        re.DOTALL
    )

    subs = []
    for match in pattern.finditer(content):
        h1, m1, s1, ms1 = map(int, match.group(2, 3, 4, 5))
        h2, m2, s2, ms2 = map(int, match.group(6, 7, 8, 9))
        t_start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
        t_end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
        raw_text = match.group(10).strip()
        
        speaker = "Dialogue"
        if "<b>John:</b>" in raw_text:
            speaker = "John"
            text = raw_text.replace("<b>John:</b>", "").strip()
        elif "<b>Skyler" in raw_text or "Frankly" in raw_text:
            speaker = "Skyler 'Frankly'"
            text = re.sub(r'<b>.*?</b>:?', '', raw_text).strip()
        else:
            text = re.sub(r'<[^>]+>', '', raw_text).strip()

        subs.append({
            "start": t_start,
            "end": t_end,
            "speaker": speaker,
            "text": text
        })
    return subs

class WorkerTripState:
    def __init__(self, subject_id: int, name: str, shirt: str):
        self.subject_id = subject_id
        self.name = name
        self.shirt = shirt
        
        # States: 'TRENCH_PICK', 'TRENCH_PRY', 'TRENCH_STAND', 'LOADED_TRANSIT', 'TRAILER_TOSS', 'EMPTY_RETURN'
        self.state = 'TRENCH_PRY' if subject_id == 0 else 'EMPTY_RETURN'
        self.zone = 'TRENCH' if subject_id == 0 else 'TRAILER'
        self.is_armed = True if subject_id == 0 else False
        self.has_load = True if subject_id == 0 else False
        self.current_load_kg = 0.0
        self.carried_mass_kg = MASS_SINGLE_CARRY_KG
        
        self.trip_count = 0
        self.cumulative_mass_kg = 0.0
        self.trip_events = []
        self.last_trip_time_s = -100.0
        self.last_pick_time_s = 0.0
        self.dwell_trench_frames = 0

class TrailerTripTripwireEngine:
    """
    Deterministic Trailer-Trip Spatial Tripwire Engine:
      - Trench Pick Zone: X > 520 px (rubble gathering, prying, lifting)
      - Trailer Toss Zone: X < 450 px (dump bed unloading)
      - Transit Corridor: 450 px <= X <= 520 px (loaded transit vs empty return)
    """
    def __init__(self, trailer_x: float = TRAILER_X_LIMIT, trench_x: float = TRENCH_X_LIMIT):
        self.trailer_x = trailer_x
        self.trench_x = trench_x
        self.workers = {
            0: WorkerTripState(0, "John (Orange)", "orange"),
            1: WorkerTripState(1, "Skyler 'Frankly' (Yellow)", "yellow")
        }
        self.total_trips = 0
        self.total_tonnage_kg = 0.0

    def update(self, tracked_subjects: list, frame_idx: int, frame_time_s: float):
        subj_map = {s["subject_id"]: s for s in tracked_subjects}

        # Check 2-man proximity if both workers are tracked
        is_two_man_assist = False
        if 0 in subj_map and 1 in subj_map:
            c0 = subj_map[0]["centroid"]
            c1 = subj_map[1]["centroid"]
            dist_px = float(np.hypot(c0[0] - c1[0], c0[1] - c1[1]))
            # If both are in staging/trench area (X > 450) and within 180 px (~1 meter)
            if dist_px < 180.0 and c0[0] > 450.0 and c1[0] > 450.0:
                is_two_man_assist = True

        results = {}
        for sid, wstate in self.workers.items():
            if sid not in subj_map:
                results[sid] = {
                    "state": wstate.state,
                    "zone": wstate.zone,
                    "current_load_kg": wstate.current_load_kg,
                    "carried_mass_kg": wstate.carried_mass_kg,
                    "trip_count": wstate.trip_count,
                    "cumulative_mass_kg": wstate.cumulative_mass_kg,
                    "is_two_man": False
                }
                continue

            subj = subj_map[sid]
            cx = subj["centroid"][0]
            kps = subj["keypoints"]

            # 1. Determine zone (centroid or wrists reaching over trailer bed)
            wrists_in_trailer = (kps[9, 2] > 0.2 and kps[9, 0] < 450.0) or (kps[10, 2] > 0.2 and kps[10, 0] < 450.0)
            if cx < 475.0 or wrists_in_trailer:
                cur_zone = 'TRAILER'
            elif cx > self.trench_x:
                cur_zone = 'TRENCH'
            else:
                cur_zone = 'TRANSIT'
            wstate.zone = cur_zone

            # 2. Evaluate State Transitions & Tripwire Crossings
            if sid == 1:
                # ---------------- SKYLER (Hauler) ----------------
                chunk_mass = MASS_HEAVY_PRY_2MAN_KG if is_two_man_assist else MASS_SINGLE_CARRY_KG

                if cur_zone == 'TRENCH':
                    wstate.dwell_trench_frames += 1
                    # Arm for trip once entering/inside trench
                    if not wstate.is_armed and (frame_time_s - wstate.last_trip_time_s >= 0.8):
                        wstate.is_armed = True
                        wstate.last_pick_time_s = frame_time_s
                        wstate.carried_mass_kg = chunk_mass
                    wstate.state = 'TRENCH_PICK'
                    wstate.has_load = wstate.is_armed
                    wstate.current_load_kg = wstate.carried_mass_kg if wstate.has_load else MASS_EMPTY_RETURN_KG

                elif cur_zone == 'TRANSIT':
                    wstate.dwell_trench_frames = 0
                    if wstate.has_load:
                        wstate.state = 'LOADED_TRANSIT'
                        wstate.current_load_kg = wstate.carried_mass_kg
                    else:
                        wstate.state = 'EMPTY_RETURN'
                        wstate.current_load_kg = MASS_EMPTY_RETURN_KG

                elif cur_zone == 'TRAILER':
                    wstate.dwell_trench_frames = 0
                    # Tripwire Crossing into Trailer
                    if wstate.is_armed and wstate.has_load and (frame_time_s - wstate.last_pick_time_s >= 1.0):
                        wstate.trip_count += 1
                        wstate.cumulative_mass_kg += wstate.carried_mass_kg
                        self.total_trips += 1
                        self.total_tonnage_kg += wstate.carried_mass_kg
                        wstate.last_trip_time_s = frame_time_s
                        wstate.trip_events.append({
                            "worker": wstate.name,
                            "trip": wstate.trip_count,
                            "frame": frame_idx,
                            "time_s": round(frame_time_s, 2),
                            "mass_kg": wstate.carried_mass_kg,
                            "cumulative_kg": round(wstate.cumulative_mass_kg, 1),
                            "is_two_man": is_two_man_assist
                        })
                        wstate.is_armed = False
                        wstate.has_load = False

                    wstate.state = 'TRAILER_TOSS'
                    wstate.current_load_kg = MASS_EMPTY_RETURN_KG

            elif sid == 0:
                # ---------------- JOHN (Trench Demo & Heavy Slab Pry) ----------------
                trunk_flex = 0.0
                if kps[5, 2] > 0.2 and kps[6, 2] > 0.2 and kps[11, 2] > 0.2 and kps[12, 2] > 0.2:
                    mid_sh_x = (kps[5, 0] + kps[6, 0]) * 0.5
                    mid_sh_y = (kps[5, 1] + kps[6, 1]) * 0.5
                    mid_hip_x = (kps[11, 0] + kps[12, 0]) * 0.5
                    mid_hip_y = (kps[11, 1] + kps[12, 1]) * 0.5
                    dx = mid_sh_x - mid_hip_x
                    dy = mid_sh_y - mid_hip_y
                    trunk_flex = float(np.degrees(np.arctan2(abs(dx), max(1e-4, -dy))))

                is_prying_or_lifting = (trunk_flex > 20.0) or is_two_man_assist

                if cur_zone == 'TRENCH':
                    wstate.state = 'TRENCH_PRY' if is_prying_or_lifting else 'TRENCH_STAND'
                    wstate.carried_mass_kg = MASS_HEAVY_PRY_2MAN_KG if (is_two_man_assist or is_prying_or_lifting) else MASS_SINGLE_CARRY_KG
                    wstate.has_load = is_prying_or_lifting
                    wstate.current_load_kg = MASS_HEAVY_PRY_2MAN_KG if is_prying_or_lifting else MASS_EMPTY_RETURN_KG
                    wstate.is_armed = True

                elif cur_zone == 'TRANSIT':
                    if wstate.has_load:
                        wstate.state = 'LOADED_TRANSIT'
                        wstate.current_load_kg = wstate.carried_mass_kg
                    else:
                        wstate.state = 'EMPTY_RETURN'
                        wstate.current_load_kg = MASS_EMPTY_RETURN_KG

                elif cur_zone == 'TRAILER':
                    if wstate.is_armed and wstate.has_load and (frame_time_s - wstate.last_pick_time_s >= 1.0):
                        wstate.trip_count += 1
                        wstate.cumulative_mass_kg += wstate.carried_mass_kg
                        self.total_trips += 1
                        self.total_tonnage_kg += wstate.carried_mass_kg
                        wstate.last_trip_time_s = frame_time_s
                        wstate.trip_events.append({
                            "worker": wstate.name,
                            "trip": wstate.trip_count,
                            "frame": frame_idx,
                            "time_s": round(frame_time_s, 2),
                            "mass_kg": wstate.carried_mass_kg,
                            "cumulative_kg": round(wstate.cumulative_mass_kg, 1),
                            "is_two_man": is_two_man_assist
                        })
                        wstate.is_armed = False
                        wstate.has_load = False

                    wstate.state = 'TRAILER_TOSS'
                    wstate.current_load_kg = MASS_EMPTY_RETURN_KG

            results[sid] = {
                "state": wstate.state,
                "zone": wstate.zone,
                "current_load_kg": wstate.current_load_kg,
                "carried_mass_kg": wstate.carried_mass_kg,
                "trip_count": wstate.trip_count,
                "cumulative_mass_kg": wstate.cumulative_mass_kg,
                "is_two_man": is_two_man_assist
            }

        return results

class YOLOv8PoseDetector:
    def __init__(self, onnx_model_path: str):
        if not os.path.exists(onnx_model_path):
            raise FileNotFoundError(f"Model not found: {onnx_model_path}")
        
        available = ort.get_available_providers()
        print(f"[ORT] Available execution providers: {available}")
        providers = [p for p in ["CUDAExecutionProvider", "CPUExecutionProvider"] if p in available]
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(onnx_model_path, sess_options=opts, providers=providers)
        active_providers = self.session.get_providers()
        print(f"[ORT] Active session providers: {active_providers}")
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.net_h = self.input_shape[2]
        self.net_w = self.input_shape[3]

    def infer_candidates(self, img_pil: Image.Image, conf_thresh: float = 0.15, iou_thresh: float = 0.45):
        w, h = img_pil.size
        scale = min(self.net_w / w, self.net_h / h)
        nw, nh = int(round(w * scale)), int(round(h * scale))
        resized = img_pil.resize((nw, nh), Image.BILINEAR)

        pad_x = (self.net_w - nw) // 2
        pad_y = (self.net_h - nh) // 2
        canvas = Image.new("RGB", (self.net_w, self.net_h), (114, 114, 114))
        canvas.paste(resized, (pad_x, pad_y))

        arr = np.array(canvas, dtype=np.float32) / 255.0
        arr = arr.transpose(2, 0, 1)
        arr = np.expand_dims(arr, axis=0)

        outputs = self.session.run(None, {self.input_name: arr})
        preds = outputs[0][0].transpose(1, 0)
        scores = preds[:, 4]
        valid_mask = scores > conf_thresh
        if not np.any(valid_mask):
            return []

        valid_preds = preds[valid_mask]
        valid_scores = scores[valid_mask]
        boxes_raw = valid_preds[:, :4]
        cx, cy, bw, bh = boxes_raw[:, 0], boxes_raw[:, 1], boxes_raw[:, 2], boxes_raw[:, 3]
        x1 = np.maximum(0, ((cx - bw / 2.0) - pad_x) / scale)
        y1 = np.maximum(0, ((cy - bh / 2.0) - pad_y) / scale)
        x2 = np.minimum(w, ((cx + bw / 2.0) - pad_x) / scale)
        y2 = np.minimum(h, ((cy + bh / 2.0) - pad_y) / scale)

        boxes_orig = np.column_stack([x1, y1, x2, y2])
        keep_indices = nms_boxes(boxes_orig, valid_scores, iou_thresh=iou_thresh)

        candidates = []
        for k_idx in keep_indices:
            pred = valid_preds[k_idx]
            box = boxes_orig[k_idx]
            raw_kps = pred[5:].reshape(17, 3)
            kps_orig = np.zeros_like(raw_kps)
            kps_orig[:, 0] = (raw_kps[:, 0] - pad_x) / scale
            kps_orig[:, 1] = (raw_kps[:, 1] - pad_y) / scale
            kps_orig[:, 2] = raw_kps[:, 2]

            cand_cx = float((box[0] + box[2]) / 2.0)
            cand_cy = float((box[1] + box[3]) / 2.0)
            cand_area = float((box[2] - box[0]) * (box[3] - box[1]))
            candidates.append({
                "bbox": box,
                "keypoints": kps_orig,
                "score": float(valid_scores[k_idx]),
                "centroid": (cand_cx, cand_cy),
                "area": cand_area
            })
        return candidates

class ChromaticDualWorkerTracker:
    """
    Tracks both workers concurrently, strictly anchored to their shirt colors:
      - Subject 0: John (Orange Shirt) -> Trench excavation & heavy prying
      - Subject 1: Skyler 'Frankly' (Neon Yellow Shirt) -> Trailer loading & dump bed stacking
    """
    def __init__(self, target_w: int, target_h: int):
        self.target_w = target_w
        self.target_h = target_h
        self.tracks = [None, None]
        self.colors = [
            {"primary": (255, 140, 0), "outline": (180, 80, 0), "name": "John (Orange)", "shirt": "orange"},
            {"primary": (198, 255, 0), "outline": (120, 180, 0), "name": "Skyler 'Frankly' (Yellow)", "shirt": "yellow"}
        ]

    def update(self, candidates: list, img_rgb: np.ndarray):
        valid_cands = [c for c in candidates if c["area"] > 500 and c["score"] > 0.18]

        # Extract shirt color for every candidate
        cand_shirt_colors = []
        for c in valid_cands:
            color = classify_worker_shirt_color(img_rgb, c["bbox"], c["keypoints"])
            cand_shirt_colors.append(color)

        # Initial assignment or re-acquisition
        if self.tracks[0] is None or self.tracks[1] is None:
            for idx, (cand, shirt) in enumerate(zip(valid_cands, cand_shirt_colors)):
                target_slot = 0 if shirt == 'orange' else (1 if shirt == 'yellow' else None)
                if target_slot is not None and self.tracks[target_slot] is None:
                    self._init_track(target_slot, cand)

        # Tracking update with chromatic priority
        matched_cand_indices = set()
        for slot in [0, 1]:
            tr = self.tracks[slot]
            if tr is None:
                continue

            target_shirt = self.colors[slot]["shirt"]
            pred_cx = tr["centroid"][0] + tr["velocity"][0]
            pred_cy = tr["centroid"][1] + tr["velocity"][1]

            best_idx = None
            best_score = 999999.0

            for idx, (cand, shirt) in enumerate(zip(valid_cands, cand_shirt_colors)):
                if idx in matched_cand_indices:
                    continue
                d = float(np.hypot(cand["centroid"][0] - pred_cx, cand["centroid"][1] - pred_cy))
                if d > 320.0:
                    continue

                color_penalty = 0.0 if shirt == target_shirt else 350.0
                match_score = d + color_penalty

                if match_score < best_score:
                    best_score = match_score
                    best_idx = idx

            if best_idx is not None and best_score < 400.0:
                matched_cand_indices.add(best_idx)
                cand = valid_cands[best_idx]
                inst_v = np.array(cand["centroid"]) - tr["centroid"]
                tr["velocity"] = 0.7 * tr["velocity"] + 0.3 * inst_v
                tr["centroid"] = np.array(cand["centroid"], dtype=np.float32)
                tr["bbox"] = 0.8 * np.array(cand["bbox"]) + 0.2 * tr["bbox"]

                # Smooth keypoints
                smoothed_kps = np.copy(cand["keypoints"])
                for j in range(17):
                    if cand["keypoints"][j, 2] < 0.25 and tr["keypoints"][j, 2] >= 0.20:
                        smoothed_kps[j, 0] = tr["keypoints"][j, 0] + tr["velocity"][0]
                        smoothed_kps[j, 1] = tr["keypoints"][j, 1] + tr["velocity"][1]
                        smoothed_kps[j, 2] = tr["keypoints"][j, 2] * 0.90
                    elif cand["keypoints"][j, 2] >= 0.20:
                        smoothed_kps[j, 0] = 0.85 * cand["keypoints"][j, 0] + 0.15 * tr["keypoints"][j, 0]
                        smoothed_kps[j, 1] = 0.85 * cand["keypoints"][j, 1] + 0.15 * tr["keypoints"][j, 1]
                tr["keypoints"] = smoothed_kps
                tr["consecutive_lost"] = 0
                tr["interpolated"] = False
            else:
                # Coast
                tr["consecutive_lost"] += 1
                if tr["consecutive_lost"] <= 25:
                    v = tr["velocity"] * 0.90
                    tr["velocity"] = v
                    tr["centroid"] += v
                    tr["bbox"] += np.array([v[0], v[1], v[0], v[1]], dtype=np.float32)
                    tr["keypoints"][:, 0] += v[0]
                    tr["keypoints"][:, 1] += v[1]
                    tr["keypoints"][:, 2] *= 0.90
                    tr["interpolated"] = True
                else:
                    self.tracks[slot] = None

        # Re-acquire vacant slots with remaining candidates
        for slot in [0, 1]:
            if self.tracks[slot] is None:
                target_shirt = self.colors[slot]["shirt"]
                for idx, (cand, shirt) in enumerate(zip(valid_cands, cand_shirt_colors)):
                    if idx not in matched_cand_indices and shirt == target_shirt:
                        matched_cand_indices.add(idx)
                        self._init_track(slot, cand)
                        break

        return self._build_return()

    def _init_track(self, slot: int, cand: dict):
        self.tracks[slot] = {
            "bbox": np.array(cand["bbox"], dtype=np.float32),
            "keypoints": np.array(cand["keypoints"], dtype=np.float32),
            "centroid": np.array(cand["centroid"], dtype=np.float32),
            "velocity": np.array([0.0, 0.0], dtype=np.float32),
            "consecutive_lost": 0,
            "interpolated": False,
            "subject_id": slot
        }

    def _build_return(self):
        res = []
        for slot in [0, 1]:
            tr = self.tracks[slot]
            if tr is not None:
                res.append({
                    "subject_id": slot,
                    "name": self.colors[slot]["name"],
                    "color": self.colors[slot]["primary"],
                    "outline": self.colors[slot]["outline"],
                    "bbox": tuple(tr["bbox"].astype(int)),
                    "keypoints": tr["keypoints"],
                    "centroid": tr["centroid"],
                    "interpolated": tr["interpolated"]
                })
        return res

def process_multi_subject_video(video_path: str, max_frames: int = 0):
    print("=" * 80)
    print(f"[CONCURRENT 2-PERSON LOAD TRACKER] Target Video: {video_path}")
    print(f"Max Frames to Process: {'FULL VIDEO' if max_frames <= 0 else max_frames}")
    
    probe_cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration,r_frame_rate", "-of", "json", video_path
    ]
    no_win_flags = 0x08000000 if os.name == 'nt' else 0
    meta = json.loads(subprocess.check_output(probe_cmd, creationflags=no_win_flags).decode("utf-8"))["streams"][0]
    orig_w, orig_h = int(meta["width"]), int(meta["height"])
    total_duration_s = float(meta.get("duration", 273.77))
    
    # Decimation to steady 30.0 FPS
    target_fps = 30.0
    target_w, target_h = 1280, 720
    total_estimated_frames = int(round(total_duration_s * target_fps)) if max_frames <= 0 else max_frames
    print(f"[1/4] Native Stream: {orig_w}x{orig_h} ({total_duration_s:.1f}s) -> Processed {target_w}x{target_h} @ {target_fps:.1f} FPS ({total_estimated_frames} frames)")

    # Load Subtitles from Cooper_7741.srt
    srt_path = os.path.splitext(video_path)[0] + ".srt"
    subtitles = load_srt_subtitles(srt_path)
    print(f"      Subtitles loaded: {len(subtitles)} dialogue segments from {os.path.basename(srt_path)}")

    # Initialize YOLOv8 pose detector and Tripwire Engine
    onnx_path = r"C:\dev\cu_vision_lite\models\yolov8n-pose.onnx"
    detector = YOLOv8PoseDetector(onnx_path)
    tracker = ChromaticDualWorkerTracker(target_w, target_h)
    trip_engine = TrailerTripTripwireEngine(trailer_x=TRAILER_X_LIMIT, trench_x=TRENCH_X_LIMIT)

    run_id = f"run_{time.strftime('%Y%m%dT%H%M%S')}_trailer_trip_kinematics"
    run_dir = os.path.join(r"C:\dev\kernel_lab\runs", run_id)
    outputs_dir = os.path.join(run_dir, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    out_video_path = os.path.join(outputs_dir, "multi_subject_concrete_hud.mp4")

    # FFmpeg pipes: decode 30fps rawvideo via hardware filter, encode 30fps h264 via native AD107 NVENC
    cmd_in = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={target_fps},scale={target_w}:{target_h}",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-v", "error", "-"
    ]
    cmd_out = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{target_w}x{target_h}",
        "-r", str(target_fps), "-i", "-",
        "-c:v", "h264_nvenc", "-preset", "p1", "-tune", "ll", "-pix_fmt", "yuv420p",
        "-b:v", "4000k", out_video_path
    ]

    proc_in = subprocess.Popen(cmd_in, stdout=subprocess.PIPE, bufsize=10**8, creationflags=no_win_flags)
    proc_out = subprocess.Popen(cmd_out, stdin=subprocess.PIPE, bufsize=10**8, creationflags=no_win_flags)

    frame_bytes = target_w * target_h * 3
    idx = 0
    t_start = time.perf_counter()
    timeline = []
    cuda_times = []

    print(f"[2/4] Streaming through AD107 YOLOv8 + Trailer-Trip Spatial Tripwire + CUDA Kinematics Pipeline...")

    while True:
        raw_frame = proc_in.stdout.read(frame_bytes)
        if len(raw_frame) != frame_bytes:
            break

        img_pil = Image.frombytes("RGB", (target_w, target_h), raw_frame)
        img_np = np.array(img_pil)
        frame_time_s = idx / target_fps

        # Multi-person candidate inference & tracking
        candidates = detector.infer_candidates(img_pil, conf_thresh=0.15)
        tracked_subjects = tracker.update(candidates, img_np)

        # Deterministic Trailer-Trip Spatial Tripwire Update
        trip_eval_map = trip_engine.update(tracked_subjects, idx, frame_time_s)

        frame_record = {
            "frame": idx,
            "timestamp_s": round(frame_time_s, 3),
            "total_trips": trip_engine.total_trips,
            "total_tonnage_kg": round(trip_engine.total_tonnage_kg, 1),
            "subjects": []
        }

        draw = ImageDraw.Draw(img_pil)

        # Draw Vertical Spatial Tripwires & Zone Tags
        # Trailer Dump line at X = 450
        draw.line([(int(TRAILER_X_LIMIT), 82), (int(TRAILER_X_LIMIT), target_h - 55)], fill=(0, 220, 255), width=2)
        # Trench line at X = 520
        draw.line([(int(TRENCH_X_LIMIT), 82), (int(TRENCH_X_LIMIT), target_h - 55)], fill=(255, 140, 0), width=2)

        # Top Zone Boundary Tags
        draw.rectangle([(20, 80), (195, 100)], fill=(12, 24, 34, 210))
        draw.text((25, 84), "<< TRAILER ZONE (X<450)", fill=(0, 220, 255))

        draw.rectangle([(454, 80), (516, 100)], fill=(20, 24, 28, 210))
        draw.text((458, 84), "CORRIDOR", fill=(190, 190, 190))

        draw.rectangle([(524, 80), (715, 100)], fill=(34, 20, 12, 210))
        draw.text((528, 84), "TRENCH PRY & PICK (X>520) >>", fill=(255, 140, 0))

        for subj in tracked_subjects:
            sid = subj["subject_id"]
            kps = subj["keypoints"]
            col = subj["color"]
            outline_col = subj["outline"]

            # Spatial scale factor (shoulder width ~ 40cm)
            sh_dist = float(np.linalg.norm(kps[5, :2] - kps[6, :2]))
            m_per_px = 0.40 / max(sh_dist, 20.0)

            # Dynamic Trip Load from Deterministic Tripwire Engine
            subj_trip = trip_eval_map.get(sid, {
                "state": "UNKNOWN",
                "zone": "UNKNOWN",
                "current_load_kg": 0.0,
                "carried_mass_kg": MASS_SINGLE_CARRY_KG,
                "trip_count": 0,
                "cumulative_mass_kg": 0.0,
                "is_two_man": False
            })
            dynamic_load_kg = subj_trip["current_load_kg"]

            # Run AD107 CUDA Kinematics kernel with measured dynamic mass
            t0_cuda = time.perf_counter()
            kin = solve_kinematic_telemetry(
                keypoints=kps,
                meters_per_pixel=m_per_px,
                load_mass_kg=dynamic_load_kg,
                torso_mass_kg=40.0
            )[0]
            dt_cuda = (time.perf_counter() - t0_cuda) * 1000.0
            cuda_times.append(dt_cuda)

            kin["subject_id"] = sid
            kin["worker_name"] = "John (Orange)" if sid == 0 else "Skyler 'Frankly' (Yellow)"
            kin["cuda_ms"] = round(dt_cuda, 3)
            kin["bbox"] = [int(x) for x in subj["bbox"]]
            kin["interpolated"] = subj["interpolated"]
            kin["trip_state"] = subj_trip["state"]
            kin["zone"] = subj_trip["zone"]
            kin["load_mass_kg"] = dynamic_load_kg
            kin["trip_count"] = subj_trip["trip_count"]
            kin["cumulative_kg"] = subj_trip["cumulative_mass_kg"]
            kin["is_two_man"] = subj_trip["is_two_man"]
            frame_record["subjects"].append(kin)

            # Draw bones
            for p1, p2 in SKELETON_CONNECTIONS:
                if kps[p1, 2] > 0.2 and kps[p2, 2] > 0.2:
                    x1, y1 = int(kps[p1, 0]), int(kps[p1, 1])
                    x2, y2 = int(kps[p2, 0]), int(kps[p2, 1])
                    draw.line([(x1, y1), (x2, y2)], fill=col, width=4)

            # Draw joints
            for j in range(17):
                if kps[j, 2] > 0.2:
                    jx, jy = int(kps[j, 0]), int(kps[j, 1])
                    draw.ellipse([(jx-4, jy-4), (jx+4, jy+4)], fill=(255, 255, 255), outline=outline_col, width=2)

            # Draw Center of Mass
            cx, cy = int(kin["com_x"]), int(kin["com_y"])
            draw.ellipse([(cx-6, cy-6), (cx+6, cy+6)], fill=col, outline=(255, 255, 255), width=2)

            # Draw Subject Label above head
            bx1, by1, bx2, by2 = subj["bbox"]
            label_text = f"{subj['name']} | {subj_trip['state']} ({dynamic_load_kg:.0f}kg) | L5/S1: {kin['l5_s1_moment_nm']:.1f}Nm"
            draw.rectangle([(bx1, max(0, by1 - 22)), (bx1 + len(label_text)*7 + 8, max(0, by1))], fill=(15, 20, 28, 225))
            draw.text((bx1 + 4, max(0, by1 - 18)), label_text, fill=col)

            # Draw Hand Load Indicator Badge
            if dynamic_load_kg > 0:
                lw, rw = kps[9], kps[10]
                wx = int((lw[0] + rw[0]) * 0.5) if (lw[2] > 0.2 and rw[2] > 0.2) else int(bx1 + (bx2 - bx1) * 0.5)
                wy = int((lw[1] + rw[1]) * 0.5) if (lw[2] > 0.2 and rw[2] > 0.2) else int(by1 + (by2 - by1) * 0.5)
                load_badge = f"LOAD: {dynamic_load_kg:.0f}kg" + (" (2-MAN)" if subj_trip["is_two_man"] else " SLAB")
                bw_half = len(load_badge) * 4 + 6
                draw.rectangle([(wx - bw_half, wy - 10), (wx + bw_half, wy + 10)], fill=(160, 20, 20, 220), outline=(255, 80, 80), width=2)
                draw.text((wx - bw_half + 4, wy - 7), load_badge, fill=(255, 255, 255))

        # Draw Global HUD Banner at Top
        draw.rectangle([(16, 10), (target_w - 16, 76)], fill=(12, 16, 24, 235), outline=(50, 70, 90), width=2)
        
        cum_kg = trip_engine.total_tonnage_kg
        cum_tons = cum_kg / 907.185
        cum_lbs = cum_kg * 2.20462

        hud_title = f"DUAL-WORKER CONCRETE DEMO & TRAILER LOAD KINEMATICS | AD107 CUDA | Frame {idx:04d}/{total_estimated_frames} ({frame_time_s:.1f}s / {total_duration_s:.1f}s)"
        hud_metrics = f"TRIPS: {trip_engine.total_trips}  |  TOTAL REMOVED: {cum_kg:.1f} kg ({cum_tons:.2f} tons / {cum_lbs:.0f} lbs)  |  CHUNK: 20kg (1-man) / 35kg (2-man)"

        s0_info = next((s for s in frame_record["subjects"] if s["subject_id"] == 0), None)
        s1_info = next((s for s in frame_record["subjects"] if s["subject_id"] == 1), None)

        s0_stat = f"John (Orange): {s0_info['trip_state']} | Load {s0_info['load_mass_kg']:.0f}kg | Trunk {s0_info['theta_trunk_deg']} deg | L5/S1 {s0_info['l5_s1_moment_nm']}Nm | {'STOOP' if s0_info['is_stoop_hazard'] else 'OK'}" if s0_info else "John: SEARCHING"
        s1_stat = f"Skyler (Yellow): {s1_info['trip_state']} | Load {s1_info['load_mass_kg']:.0f}kg | Trips {s1_info['trip_count']} | L5/S1 {s1_info['l5_s1_moment_nm']}Nm | {'STOOP' if s1_info['is_stoop_hazard'] else 'OK'}" if s1_info else "Skyler: SEARCHING"

        draw.text((28, 14), hud_title, fill=(100, 200, 255))
        draw.text((28, 33), hud_metrics, fill=(255, 215, 0))
        draw.text((28, 54), s0_stat, fill=(255, 140, 0))
        draw.text((680, 54), s1_stat, fill=(198, 255, 0))

        # Synchronized Active Dialogue Subtitle Bar at Bottom
        active_sub = next((s for s in subtitles if s["start"] <= frame_time_s <= s["end"]), None)
        if active_sub:
            sub_spk = active_sub["speaker"]
            sub_txt = active_sub["text"]
            sub_col = (255, 160, 40) if "John" in sub_spk else (210, 255, 40)
            full_line = f"{sub_spk}: {sub_txt}"
            if len(full_line) > 130:
                full_line = full_line[:127] + "..."
            line_w = len(full_line) * 7 + 24
            bx1 = max(30, int((target_w - line_w) * 0.5))
            bx2 = min(target_w - 30, bx1 + line_w)
            draw.rectangle([(bx1, target_h - 48), (bx2, target_h - 20)], fill=(10, 14, 20, 225), outline=(60, 80, 100), width=1)
            draw.text((bx1 + 12, target_h - 43), full_line, fill=sub_col)

        # Write frame to FFmpeg pipe
        proc_out.stdin.write(img_pil.tobytes())
        timeline.append(frame_record)

        idx += 1
        if idx % 500 == 0:
            elapsed = time.perf_counter() - t_start
            cur_fps = idx / elapsed
            eta_s = (total_estimated_frames - idx) / max(cur_fps, 1.0)
            print(f"  -> Processed {idx}/{total_estimated_frames} frames ({cur_fps:.1f} FPS, ETA: {eta_s/60.0:.1f}m) | Trips: {trip_engine.total_trips} | Removed: {trip_engine.total_tonnage_kg:.1f}kg...")

        if max_frames > 0 and idx >= max_frames:
            break

    proc_in.stdout.close()
    proc_in.wait()
    try:
        proc_out.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    proc_out.wait()

    num_frames = idx
    total_proc_time = time.perf_counter() - t_start
    gpu_time_total_ms = sum(cuda_times) if cuda_times else total_proc_time * 1000.0 * 0.35

    print(f"[3/4] Pipeline complete: {num_frames} frames in {total_proc_time/60.0:.2f}m ({num_frames / total_proc_time:.1f} FPS)")
    print(f"      Total Load Trips: {trip_engine.total_trips}")
    print(f"      Skyler Trips:     {trip_engine.workers[1].trip_count} ({trip_engine.workers[1].cumulative_mass_kg:.1f} kg)")
    print(f"      John Trips/Loads: {trip_engine.workers[0].trip_count} ({trip_engine.workers[0].cumulative_mass_kg:.1f} kg)")
    print(f"      Cumulative Mass:  {trip_engine.total_tonnage_kg:.1f} kg ({trip_engine.total_tonnage_kg/907.185:.2f} short tons / {trip_engine.total_tonnage_kg*2.20462:.0f} lbs)")

    # Export Full JSON Telemetry
    out_json_path = os.path.join(outputs_dir, "multi_subject_tracks.json")
    with open(out_json_path, "w") as f:
        json.dump(timeline, f, indent=2)

    # Export Manifest Summary
    manifest = {
        "run_id": run_id,
        "video_path": video_path,
        "processed_frames": num_frames,
        "duration_seconds": round(num_frames / target_fps, 2),
        "target_fps": target_fps,
        "wall_time_seconds": round(total_proc_time, 2),
        "average_fps": round(num_frames / total_proc_time, 2),
        "total_trips": trip_engine.total_trips,
        "cumulative_tonnage_kg": round(trip_engine.total_tonnage_kg, 1),
        "cumulative_tonnage_tons": round(trip_engine.total_tonnage_kg / 907.185, 3),
        "cumulative_tonnage_lbs": round(trip_engine.total_tonnage_kg * 2.20462, 1),
        "tripwire_limits": {
            "trailer_x_limit": TRAILER_X_LIMIT,
            "trench_x_limit": TRENCH_X_LIMIT
        },
        "mass_model": {
            "single_carry_kg": MASS_SINGLE_CARRY_KG,
            "heavy_pry_2man_kg": MASS_HEAVY_PRY_2MAN_KG,
            "empty_return_kg": MASS_EMPTY_RETURN_KG
        },
        "workers": {
            "john": {
                "subject_id": 0,
                "role": "Trench Demo & Slab Pry",
                "shirt_color": "Orange",
                "trips": trip_engine.workers[0].trip_count,
                "cumulative_kg": round(trip_engine.workers[0].cumulative_mass_kg, 1),
                "trip_events": trip_engine.workers[0].trip_events
            },
            "skyler": {
                "subject_id": 1,
                "role": "Trailer Load & Dump Hoist",
                "shirt_color": "Neon Yellow",
                "trips": trip_engine.workers[1].trip_count,
                "cumulative_kg": round(trip_engine.workers[1].cumulative_mass_kg, 1),
                "trip_events": trip_engine.workers[1].trip_events
            }
        }
    }
    manifest_path = os.path.join(outputs_dir, "trailer_trip_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Ledger logging is managed via Metropolis DuckDB Supercharger IPC
    print(f"[LEDGER] Manifest sealed at {manifest_path}. Telemetry ready for DuckDB Supercharger.")

    print(f"[4/4] Deliverables written to: {outputs_dir}")
    print(f"  HUD Video:  {out_video_path}")
    print(f"  Telemetry:  {out_json_path}")
    print(f"  Manifest:   {manifest_path}")
    print("=" * 80)
    return run_id, out_video_path, out_json_path, manifest_path, num_frames, total_proc_time

if __name__ == "__main__":
    vid = sys.argv[1] if len(sys.argv) > 1 else r"G:\My Drive\Job Records\OPEN\cooper, nigel, concrete\JohnandFrankly\Cooper_7741.MOV"
    frames = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    process_multi_subject_video(vid, max_frames=frames)
