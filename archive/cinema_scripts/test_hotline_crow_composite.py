import os
import subprocess

FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
VIDEO_DRONE = r"C:\Users\John\Videos\sunset54\41.mov"
VIDEO_5128 = r"C:\Users\John\Videos\sunset54\IMG_5128.MOV"
VIDEO_CROWS = r"B:\crows_slowmo_centered.mp4"
OUTPUT_DIR = r"C:\Users\John\Videos\sunset54"

# Variation 1: Hotline Miami Split (Top: Crows Chroma-Keyed over Twilight Drone; Bottom: Highway 54 Dusk Drive + Laser Divider)
fc1 = (
    # Crows keyed: grey sky colorkeyed out
    "[0:v]trim=start=10:end=11,setpts=PTS-STARTPTS,"
    "scale=1920:1080,colorkey=0xD8DAD9:0.28:0.12[crows_keyed];"
    # Drone twilight top background
    "[1:v]trim=start=45:end=46,setpts=PTS-STARTPTS,"
    "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
    "colorbalance=rs=-0.08:gs=0.04:bs=0.22:rm=-0.04:gm=0.08:bm=0.14:rh=0.10:gh=0.14:bh=0.24,"
    "eq=saturation=1.45:contrast=1.30[drone_sky];"
    # Composite crows over drone sky, then crop to top panel 1920x540
    "[drone_sky][crows_keyed]overlay=0:-100:format=auto,"
    "crop=1920:540:0:150[top_panel];"
    # Highway bottom panel
    "[2:v]trim=start=14:end=15,setpts=PTS-STARTPTS,"
    "crop=2400:1350:720:0,scale=1920:1080,"
    "colorbalance=rs=0.14:gs=-0.06:bs=-0.12:rm=0.22:gm=0.02:bm=-0.10:rh=0.36:gh=0.08:bh=-0.20,"
    "eq=saturation=1.50:contrast=1.30,"
    "crop=1920:540:0:450[bot_panel];"
    # Stack panels with Hotline Miami neon laser beam
    "[top_panel][bot_panel]vstack[stacked];"
    "color=c=0x00FFFF@0.45:s=1920x16,format=rgba[glow];"
    "color=c=0xFF007F@0.85:s=1920x8,format=rgba[beam];"
    "color=c=white@1.0:s=1920x2,format=rgba[core];"
    "[stacked][glow]overlay=0:532:format=auto[v1];"
    "[v1][beam]overlay=0:536:format=auto[v2];"
    "[v2][core]overlay=0:539:format=auto[vout]"
)

cmd1 = [
    FFMPEG, "-y",
    "-i", VIDEO_CROWS,
    "-i", VIDEO_DRONE,
    "-i", VIDEO_5128,
    "-filter_complex", fc1,
    "-map", "[vout]",
    "-vframes", "1",
    os.path.join(OUTPUT_DIR, "test_hotline_crow_split1.jpg")
]

# Variation 2: Hotline Miami Split (Top: Sunset Highway with Chroma-Keyed Crows in Sky; Bottom: Grand Ave Arterial + Amber Laser)
fc2 = (
    # Crows keyed
    "[0:v]trim=start=12:end=13,setpts=PTS-STARTPTS,"
    "scale=1920:1080,colorkey=0xD8DAD9:0.28:0.12[crows_keyed2];"
    # Highway sunset
    "[1:v]trim=start=10:end=11,setpts=PTS-STARTPTS,"
    "crop=2400:1350:720:0,scale=1920:1080,"
    "colorbalance=rs=0.16:gs=-0.04:bs=-0.12:rm=0.25:gm=0.02:bm=-0.10:rh=0.40:gh=0.10:bh=-0.22,"
    "eq=saturation=1.55:contrast=1.35[hwy_sky];"
    # Composite crows into the sunset sky, crop to top panel
    "[hwy_sky][crows_keyed2]overlay=0:0:format=auto,"
    "crop=1920:540:0:100[top_panel2];"
    # Drone Grand Ave bottom panel
    "[2:v]trim=start=60:end=61,setpts=PTS-STARTPTS,"
    "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:540:0:270,"
    "colorbalance=rs=-0.06:gs=-0.08:bs=0.22:rm=0.14:gm=0.02:bm=-0.08:rh=0.32:gh=0.08:bh=-0.16,"
    "eq=saturation=1.40:contrast=1.28[bot_panel2];"
    # Stack panels with amber laser
    "[top_panel2][bot_panel2]vstack[stacked2];"
    "color=c=0xFF3300@0.45:s=1920x16,format=rgba[glow2];"
    "color=c=0xFF6600@0.85:s=1920x8,format=rgba[beam2];"
    "color=c=white@1.0:s=1920x2,format=rgba[core2];"
    "[stacked2][glow2]overlay=0:532:format=auto[v21];"
    "[v21][beam2]overlay=0:536:format=auto[v22];"
    "[v22][core2]overlay=0:539:format=auto[vout2]"
)

cmd2 = [
    FFMPEG, "-y",
    "-i", VIDEO_CROWS,
    "-i", VIDEO_5128,
    "-i", VIDEO_DRONE,
    "-filter_complex", fc2,
    "-map", "[vout2]",
    "-vframes", "1",
    os.path.join(OUTPUT_DIR, "test_hotline_crow_split2.jpg")
]

print("Rendering test frames...")
subprocess.run(cmd1, check=True)
subprocess.run(cmd2, check=True)
print("Complete.")
