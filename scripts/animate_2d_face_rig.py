"""
animate_2d_face_rig.py — Native AD107 2D Camera-Locked Face Puppeteering Engine
Kernel Lab / Metropolis Architecture

Loads 2d106det face tracking JSON telemetry, computes scale- and rotation-invariant
jaw openness and eye blink ratios, and animates a stylized 2D character face rig
with real-time Shape Keys in Blender 5.2 LTS over persistent worker IPC.
"""

import argparse
import json
import math
import os
import sys
from typing import Any, Dict, List, Tuple


def euclidean_dist(p1: List[float], p2: List[float]) -> float:
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def clamp(val: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, val))


def quantile(sorted_vals: List[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * q
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    d0 = sorted_vals[int(f)] * (c - k)
    d1 = sorted_vals[int(c)] * (k - f)
    return d0 + d1


def extract_telemetry(json_path: str) -> Dict[str, Any]:
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Tracking JSON not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    frames = data.get("frames", [])
    width = data.get("width", 1920)
    height = data.get("height", 1080)
    fps = data.get("fps", 30)

    raw_frames = []
    jaw_raw_list = []
    blink_l_raw_list = []
    blink_r_raw_list = []

    for item in frames:
        if not item.get("valid", False):
            raw_frames.append({"valid": False, "frame": item.get("frame", 0)})
            continue

        lms = item.get("landmarks_2d", [])
        if len(lms) < 106:
            raw_frames.append({"valid": False, "frame": item.get("frame", 0)})
            continue

        # 2d106det landmarks
        chin = lms[16]          # Chin tip
        sellion = lms[72]       # Top of nose bridge / sellion
        inner_lip_top = lms[65] # Inner upper lip center
        inner_lip_bot = lms[69] # Inner lower lip center

        eye_l_outer = lms[86]
        eye_l_inner = lms[92]
        eye_l_top = lms[89]
        eye_l_bot = lms[94]

        eye_r_inner = lms[96]
        eye_r_outer = lms[102]
        eye_r_top = lms[99]
        eye_r_bot = lms[104]

        # Invariant distances
        face_h = max(euclidean_dist(chin, sellion), 1.0)
        mouth_gap = euclidean_dist(inner_lip_top, inner_lip_bot)
        jaw_ratio = mouth_gap / face_h

        eye_l_w = max(euclidean_dist(eye_l_outer, eye_l_inner), 1.0)
        eye_l_h = euclidean_dist(eye_l_top, eye_l_bot)
        blink_ratio_l = eye_l_h / eye_l_w

        eye_r_w = max(euclidean_dist(eye_r_outer, eye_r_inner), 1.0)
        eye_r_h = euclidean_dist(eye_r_top, eye_r_bot)
        blink_ratio_r = eye_r_h / eye_r_w

        # Screen position (normalized -0.5 to 0.5)
        head_box = item.get("head_box", [width / 2.0, height / 2.0, 100.0])
        px = head_box[0]
        py = head_box[1]
        u = (px - width / 2.0) / width
        v = -((py - height / 2.0) / height)  # invert Y for Blender 3D up

        # 2D Roll Angle (radians)
        roll = math.atan2(eye_r_inner[1] - eye_l_inner[1], eye_r_inner[0] - eye_l_inner[0])

        # Inter-ocular distance for scale
        interocular = euclidean_dist(eye_l_inner, eye_r_inner)

        raw_frames.append({
            "valid": True,
            "frame": item.get("frame", 0),
            "u": u,
            "v": v,
            "roll": roll,
            "interocular": interocular,
            "jaw_ratio": jaw_ratio,
            "blink_l": blink_ratio_l,
            "blink_r": blink_ratio_r,
        })

        jaw_raw_list.append(jaw_ratio)
        blink_l_raw_list.append(blink_ratio_l)
        blink_r_raw_list.append(blink_ratio_r)

    # Compute robust percentile thresholds for normalization
    jaw_raw_list.sort()
    blink_l_raw_list.sort()
    blink_r_raw_list.sort()

    jaw_rest = quantile(jaw_raw_list, 0.05) if jaw_raw_list else 0.05
    jaw_max = quantile(jaw_raw_list, 0.95) if jaw_raw_list else 0.25
    if jaw_max <= jaw_rest:
        jaw_max = jaw_rest + 0.1

    blink_l_min = quantile(blink_l_raw_list, 0.05) if blink_l_raw_list else 0.1
    blink_l_max = quantile(blink_l_raw_list, 0.95) if blink_l_raw_list else 0.35
    if blink_l_max <= blink_l_min:
        blink_l_max = blink_l_min + 0.1

    blink_r_min = quantile(blink_r_raw_list, 0.05) if blink_r_raw_list else 0.1
    blink_r_max = quantile(blink_r_raw_list, 0.95) if blink_r_raw_list else 0.35
    if blink_r_max <= blink_r_min:
        blink_r_max = blink_r_min + 0.1

    baseline_span = quantile([f["interocular"] for f in raw_frames if f.get("valid")], 0.5) if jaw_raw_list else 100.0

    # Build normalized output timeline
    timeline = []
    for f in raw_frames:
        if not f.get("valid"):
            timeline.append({
                "frame": f["frame"] + 1,
                "valid": False,
                "u": 0.0,
                "v": 0.0,
                "roll": 0.0,
                "scale": 1.0,
                "mouth_open": 0.0,
                "eye_blink_l": 0.0,
                "eye_blink_r": 0.0
            })
            continue

        mouth_weight = clamp((f["jaw_ratio"] - jaw_rest) / (jaw_max - jaw_rest), 0.0, 1.0)
        # Blink weight: 1.0 = fully closed, 0.0 = fully open
        blink_w_l = 1.0 - clamp((f["blink_l"] - blink_l_min) / (blink_l_max - blink_l_min), 0.0, 1.0)
        blink_w_r = 1.0 - clamp((f["blink_r"] - blink_r_min) / (blink_r_max - blink_r_min), 0.0, 1.0)
        scale = f["interocular"] / max(baseline_span, 1.0)

        timeline.append({
            "frame": f["frame"] + 1,
            "valid": True,
            "u": f["u"],
            "v": f["v"],
            "roll": f["roll"],
            "scale": scale,
            "mouth_open": round(mouth_weight, 4),
            "eye_blink_l": round(blink_w_l, 4),
            "eye_blink_r": round(blink_w_r, 4),
        })

    return {
        "width": width,
        "height": height,
        "fps": fps,
        "total_frames": len(timeline),
        "valid_count": len(jaw_raw_list),
        "calibration": {
            "jaw_rest": round(jaw_rest, 4),
            "jaw_max": round(jaw_max, 4),
            "blink_l_range": [round(blink_l_min, 4), round(blink_l_max, 4)],
            "blink_r_range": [round(blink_r_min, 4), round(blink_r_max, 4)],
            "baseline_span": round(baseline_span, 2)
        },
        "timeline": timeline
    }


def generate_bpy_rig_script(telemetry: Dict[str, Any], z_depth: float = -2.0) -> str:
    timeline = telemetry["timeline"]
    total_frames = telemetry["total_frames"]
    fps = telemetry.get("fps", 30)

    # Encode timeline as compact JSON within the script
    compact_timeline = json.dumps(timeline)

    bpy_code = f"""
import bpy
import json
import math

timeline = json.loads('''{compact_timeline}''')
Z_DEPTH = {z_depth}

scene = bpy.context.scene
scene.render.fps = {fps}
scene.frame_start = 1
scene.frame_end = {total_frames}

cam_obj = scene.camera
if not cam_obj:
    for obj in scene.objects:
        if obj.type == 'CAMERA':
            cam_obj = obj
            scene.camera = obj
            break
if not cam_obj:
    raise RuntimeError("Camera not found in active scene")

cam = cam_obj.data
sw = cam.sensor_width
f_mm = cam.lens
aspect = scene.render.resolution_x / scene.render.resolution_y
fov_x = 2.0 * math.atan((sw / 2.0) / f_mm)
fov_y = 2.0 * math.atan(((sw / aspect) / 2.0) / f_mm)
span_x = 2.0 * abs(Z_DEPTH) * math.tan(fov_x / 2.0)
span_y = 2.0 * abs(Z_DEPTH) * math.tan(fov_y / 2.0)

# Purge previous character puppet objects
for name in ["Face_Puppet_Root", "Puppet_Head_Card", "Puppet_Mouth", "Puppet_Eyes", "Puppet_Brows"]:
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

# 1. Create Root Empty parented to camera
root_obj = bpy.data.objects.new("Face_Puppet_Root", None)
root_obj.empty_display_type = 'ARROWS'
root_obj.empty_display_size = 0.2
root_obj.parent = cam_obj
scene.collection.objects.link(root_obj)

# Helper material creator
def get_or_create_mat(name, color):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = color
            bsdf.inputs['Roughness'].default_value = 0.4
    return mat

mat_skin = get_or_create_mat("Mat_Puppet_Skin", (0.95, 0.76, 0.65, 1.0))
mat_mouth_dark = get_or_create_mat("Mat_Puppet_MouthDark", (0.15, 0.04, 0.05, 1.0))
mat_teeth = get_or_create_mat("Mat_Puppet_Teeth", (0.98, 0.98, 0.98, 1.0))
mat_eyes = get_or_create_mat("Mat_Puppet_Eyes", (0.08, 0.45, 0.85, 1.0))
mat_brows = get_or_create_mat("Mat_Puppet_Brows", (0.20, 0.12, 0.08, 1.0))

# 2. Head Silhouette Mesh (Stylized oval card)
head_mesh = bpy.data.meshes.new("Puppet_Head_Mesh")
head_obj = bpy.data.objects.new("Puppet_Head_Card", head_mesh)
head_obj.parent = root_obj
scene.collection.objects.link(head_obj)

# 8-gon rounded face card
r = 0.42
verts_head = []
for i in range(12):
    ang = 2.0 * math.pi * i / 12.0
    vx = r * math.cos(ang) * 0.85
    vy = r * math.sin(ang) * 1.15
    verts_head.append((vx, vy, 0.0))
faces_head = [list(range(12))]
head_mesh.from_pydata(verts_head, [], faces_head)
head_mesh.update()
head_obj.data.materials.append(mat_skin)

# 3. Dynamic Mouth Mesh with Shape Keys
mouth_mesh = bpy.data.meshes.new("Puppet_Mouth_Mesh")
mouth_obj = bpy.data.objects.new("Puppet_Mouth", mouth_mesh)
mouth_obj.parent = root_obj
mouth_obj.location = (0.0, -0.22, 0.01)
scene.collection.objects.link(mouth_obj)

# Closed mouth resting line / slit
verts_mouth_rest = [
    (-0.16,  0.01, 0.0), # 0: left corner
    (-0.08,  0.03, 0.0), # 1: upper left
    ( 0.00,  0.04, 0.0), # 2: upper mid
    ( 0.08,  0.03, 0.0), # 3: upper right
    ( 0.16,  0.01, 0.0), # 4: right corner
    ( 0.08, -0.01, 0.0), # 5: lower right
    ( 0.00, -0.01, 0.0), # 6: lower mid
    (-0.08, -0.01, 0.0), # 7: lower left
]
faces_mouth = [[0, 1, 2, 3, 4, 5, 6, 7]]
mouth_mesh.from_pydata(verts_mouth_rest, [], faces_mouth)
mouth_mesh.update()
mouth_obj.data.materials.append(mat_mouth_dark)

# Shape keys for mouth
sk_mouth_basis = mouth_obj.shape_key_add(name="Basis")
sk_mouth_open = mouth_obj.shape_key_add(name="Mouth_Open")

# In Mouth_Open: drop lower vertices down and spread aperture
sk_mouth_open.data[5].co = ( 0.10, -0.14, 0.0)
sk_mouth_open.data[6].co = ( 0.00, -0.16, 0.0)
sk_mouth_open.data[7].co = (-0.10, -0.14, 0.0)
sk_mouth_open.data[2].co = ( 0.00,  0.07, 0.0)

# 4. Dynamic Eyes Mesh with Left/Right Blink Shape Keys
eyes_mesh = bpy.data.meshes.new("Puppet_Eyes_Mesh")
eyes_obj = bpy.data.objects.new("Puppet_Eyes", eyes_mesh)
eyes_obj.parent = root_obj
eyes_obj.location = (0.0, 0.10, 0.01)
scene.collection.objects.link(eyes_obj)

# Left eye quad and Right eye quad
verts_eyes_rest = [
    # Left eye (x: -0.20 to -0.08, y: -0.06 to 0.06)
    (-0.20, -0.06, 0.0), (-0.08, -0.06, 0.0), (-0.08, 0.06, 0.0), (-0.20, 0.06, 0.0),
    # Right eye (x: 0.08 to 0.20, y: -0.06 to 0.06)
    ( 0.08, -0.06, 0.0), ( 0.20, -0.06, 0.0), ( 0.20, 0.06, 0.0), ( 0.08, 0.06, 0.0),
]
faces_eyes = [[0, 1, 2, 3], [4, 5, 6, 7]]
eyes_mesh.from_pydata(verts_eyes_rest, [], faces_eyes)
eyes_mesh.update()
eyes_obj.data.materials.append(mat_eyes)

sk_eyes_basis = eyes_obj.shape_key_add(name="Basis")
sk_blink_l = eyes_obj.shape_key_add(name="Eye_Blink_L")
sk_blink_r = eyes_obj.shape_key_add(name="Eye_Blink_R")

# In Eye_Blink_L: flatten top vertices of left eye down to bottom line
sk_blink_l.data[2].co = (-0.08, -0.05, 0.0)
sk_blink_l.data[3].co = (-0.20, -0.05, 0.0)

# In Eye_Blink_R: flatten top vertices of right eye down to bottom line
sk_blink_r.data[6].co = ( 0.20, -0.05, 0.0)
sk_blink_r.data[7].co = ( 0.08, -0.05, 0.0)

# 5. Eyebrows
brows_mesh = bpy.data.meshes.new("Puppet_Brows_Mesh")
brows_obj = bpy.data.objects.new("Puppet_Brows", brows_mesh)
brows_obj.parent = root_obj
brows_obj.location = (0.0, 0.22, 0.01)
scene.collection.objects.link(brows_obj)

verts_brows = [
    (-0.22, 0.0, 0.0), (-0.08, 0.04, 0.0), (-0.08, 0.06, 0.0), (-0.22, 0.02, 0.0),
    ( 0.08, 0.04, 0.0), ( 0.22, 0.0, 0.0), ( 0.22, 0.02, 0.0), ( 0.08, 0.06, 0.0),
]
faces_brows = [[0, 1, 2, 3], [4, 5, 6, 7]]
brows_mesh.from_pydata(verts_brows, [], faces_brows)
brows_mesh.update()
brows_obj.data.materials.append(mat_brows)

# 6. Apply Animation Keyframes
for item in timeline:
    f_idx = item["frame"]
    scene.frame_set(f_idx)

    if not item.get("valid", False):
        continue

    # Camera-space position
    x_cam = item["u"] * span_x
    y_cam = item["v"] * span_y
    root_obj.location = (x_cam, y_cam, Z_DEPTH)
    root_obj.keyframe_insert(data_path="location", frame=f_idx)

    # 2D Roll rotation around Z
    root_obj.rotation_euler = (0.0, 0.0, item["roll"])
    root_obj.keyframe_insert(data_path="rotation_euler", frame=f_idx)

    # Scale
    s = item["scale"]
    root_obj.scale = (s, s, s)
    root_obj.keyframe_insert(data_path="scale", frame=f_idx)

    # Shape Key: Mouth Open
    sk_mouth_open.value = item["mouth_open"]
    sk_mouth_open.keyframe_insert(data_path="value", frame=f_idx)

    # Shape Key: Left Blink
    sk_blink_l.value = item["eye_blink_l"]
    sk_blink_l.keyframe_insert(data_path="value", frame=f_idx)

    # Shape Key: Right Blink
    sk_blink_r.value = item["eye_blink_r"]
    sk_blink_r.keyframe_insert(data_path="value", frame=f_idx)

scene.frame_set(1)

RESULT = {{
    "status": "ok",
    "total_keyframes": len(timeline),
    "rig_objects": ["Face_Puppet_Root", "Puppet_Head_Card", "Puppet_Mouth", "Puppet_Eyes", "Puppet_Brows"],
    "shape_keys": ["Mouth_Open", "Eye_Blink_L", "Eye_Blink_R"]
}}
"""
    return bpy_code


def main():
    parser = argparse.ArgumentParser(description="2D Camera-Locked Face Puppeteering Animation Engine")
    parser.add_argument("--json", required=True, help="Path to 2d106det face_tracks.json")
    parser.add_argument("--z-depth", type=float, default=-2.0, help="Camera-plane depth (default: -2.0m)")
    parser.add_argument("--out-bpy", default=None, help="Save generated BPY script to path")
    args = parser.parse_args()

    print(f"[*] Ingesting face tracking telemetry: {args.json}")
    telemetry = extract_telemetry(args.json)
    print(f"[+] Total frames: {telemetry['total_frames']} ({telemetry['valid_count']} valid)")
    print(f"[+] Calibration: {telemetry['calibration']}")

    bpy_code = generate_bpy_rig_script(telemetry, z_depth=args.z_depth)

    if args.out_bpy:
        with open(args.out_bpy, "w", encoding="utf-8") as f:
            f.write(bpy_code)
        print(f"[+] Saved generated BPY script: {args.out_bpy}")

    print("[*] Ready for execution via blender-mcp-server:blender_eval_bpy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
