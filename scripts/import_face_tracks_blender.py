"""
import_face_tracks_blender.py — Ingests video_face_tracker JSON into Blender 5.2 LTS
Creates a keyframed 3D Empty ('Head_Anchor') parented to the active Camera,
computing perspective pinhole depth and 6-DoF orientation per frame.
"""

import bpy
import json
import math
import os

def import_face_tracks(
    json_path: str,
    video_path: str = None,
    empty_name: str = "Head_Anchor",
    head_diameter_m: float = 0.20
):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Track JSON not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scene = bpy.context.scene
    cam_obj = scene.camera
    if not cam_obj:
        for obj in scene.objects:
            if obj.type == 'CAMERA':
                cam_obj = obj
                scene.camera = obj
                break
    if not cam_obj:
        raise RuntimeError("No camera found in active Blender scene.")

    cam = cam_obj.data
    W = scene.render.resolution_x
    H = scene.render.resolution_y
    f_mm = cam.lens
    sw_mm = cam.sensor_width
    fx = (f_mm / sw_mm) * W
    cx = W / 2.0
    cy = H / 2.0

    # Ensure / create tracking Empty
    empty = bpy.data.objects.get(empty_name)
    if not empty:
        empty = bpy.data.objects.new(empty_name, None)
        empty.empty_display_type = 'ARROWS'
        empty.empty_display_size = 0.25
        scene.collection.objects.link(empty)

    empty.parent = cam_obj
    empty.rotation_mode = 'XYZ'

    frames = data.get("frames", [])
    for item in frames:
        f_idx = item["frame"] + 1  # Blender 1-indexed frames
        scene.frame_set(f_idx)

        hb = item["head_box"]
        px = hb[0]
        py = hb[1]
        scale = max(hb[2], 1.0)

        # Compute pinhole depth and camera-space coordinates
        z_depth = (fx * head_diameter_m) / scale
        x_cam = ((px - cx) / fx) * z_depth
        y_cam = -((py - cy) / fx) * z_depth  # Invert Y for Blender 3D up
        z_cam = -z_depth                     # Camera looks along -Z

        empty.location = (x_cam, y_cam, z_cam)
        empty.keyframe_insert(data_path="location", frame=f_idx)

        pose = item.get("pose", {})
        pitch_rad = math.radians(pose.get("pitch", 0.0))
        yaw_rad = math.radians(pose.get("yaw", 0.0))
        roll_rad = math.radians(pose.get("roll", 0.0))

        empty.rotation_euler = (pitch_rad, yaw_rad, roll_rad)
        empty.keyframe_insert(data_path="rotation_euler", frame=f_idx)

    scene.frame_start = 1
    scene.frame_end = len(frames)
    scene.frame_set(1)

    # Optional: Attach video to Camera Background
    if video_path and os.path.exists(video_path):
        cam.show_background_images = True
        cam.background_images.clear()
        bg = cam.background_images.new()
        bg.source = 'MOVIE_CLIP'
        bg.clip = bpy.data.movieclips.load(video_path)
        bg.alpha = 0.8

    print(f"[OK] Successfully imported {len(frames)} frames into '{empty_name}'.")

if __name__ == "__main__":
    JSON_PATH = r"C:/dev/kernel_lab/runs/run_20261006T075805_video_face_tracker/outputs/face_tracks.json"
    VIDEO_PATH = r"C:/dev/kernel_lab/runs/run_20261006T075805_video_face_tracker/outputs/tracked_face.mp4"
    import_face_tracks(JSON_PATH, VIDEO_PATH)
