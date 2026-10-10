"""
render_hotline_sunset54_v7.py
==============================
Metropolis Cinema VFX Pipeline: Sunset 54 x Moonlight Samba Movement 3
Version: v7 Master Director Engine (The Opus Edit)

Narrative Architecture:
  - Act I: Sanctuary & Approach (0.00s - 17.14s)
    * Seg 00: Celestial Sanctuary - Conformal Stereographic Globe (2560x2560 borderless 16:9 orbital rotation)
    * Seg 01: The Dark Side Approaches - Stabilized golden hour asphalt & oncoming headlights
    * Seg 02: Tactical Split 1 - Multi-layer Tangerine/Cyan laser divider (Arterial surveillance vs Highway)
    * Seg 03: Pre-Drop Heat Bleed - Grand Ave drone dive with celluloid thermal bleed & rhythmic exposure breathing
    * [17.14s: TUTTI DROP - 3-FRAME PLANAR BGW STROBE EXPLOSION]

  - Act II: The Middle Set-Piece & Avian Breach (17.14s - 34.29s)
    * Seg 04: The Highway Breach - Stabilized twilight curve asphalt sprint
    * Seg 05: The Portal Car & Hitchcock Zolly - Isolated Grand Ave turning vehicle floating over twilight asphalt with dynamic F-curve contra-zoom pull-out
    * Seg 06: The Hero Crows - Zero-dead-frame slow-mo centered crows (B:\\crows_slowmo_centered.mp4) with Hotline Miami blood-dusk luma-split grading
    * [29.46s - 30.00s: VINYL NEEDLE SCRATCH & CHROMATIC STROBE GLITCH] - DJ back-cue needle scrub (C:\\tmp\\scratch_wicka.wav) into 3-frame chromatic burst
    * Seg 07: The Instant Track Drop / Hyperspeed Blast - 8x motion-smeared intersection hyperlapse as the full band tutti slams back in

  - Act III: Convergence & Choke (34.29s - 52.00s)
    * Seg 08: Tactical Split 2 - Percussion Breakdown with pulsing Cyan laser line
    * Seg 09: Ghost Traffic Hyperlapse - Solarized streetlight flares & 5x traffic
    * Seg 10: Final Sprint - Deep dusk bend, glowing billboards, crescent moon ahead
    * Seg 11: Climax Convergence - Stabilized midnight highway surge into crash freeze at 51.43s and CRT phosphor decay to black

Audio Pipeline:
  - Primary Soundtrack: Moonlight Samba Mvt 3 Presto Agitato (112 BPM Full Band Master)
  - SFX Layer: Vinyl needle scratch (scratch_wicka.wav) beat-locked at Bar 14 Beat 4 (29.46s)
  - Broadcast Compliance: EBU R128 (I=-16.0 LUFS, TP=-1.5 dBFS)
"""

import os
import subprocess
import sys

FFMPEG = "ffmpeg.exe"
OUTPUT_DIR = r"C:\Users\John\Videos\sunset54"
os.chdir(OUTPUT_DIR)

TRF_DIR = "trf_v7"
os.makedirs(TRF_DIR, exist_ok=True)

VIDEO_DRONE = os.path.join(OUTPUT_DIR, "41.mov")
VIDEO_5127 = os.path.join(OUTPUT_DIR, "IMG_5127.MOV")
VIDEO_5128 = os.path.join(OUTPUT_DIR, "IMG_5128.MOV")
VIDEO_CROWS = r"B:\crows_slowmo_centered.mp4"
AUDIO_PATH = r"C:\dev\CGMusicalComposition\Compositions\Moonlight_Samba_Suite\moonlight_presto_full_band_master.wav"
SCRATCH_SFX = r"C:\tmp\scratch_wicka.wav"

OUTPUT_MP4 = os.path.join(OUTPUT_DIR, "moonlight_samba_mvt3_eerie_hotline_v7.mp4")
CONTACT_JPG = os.path.join(OUTPUT_DIR, "moonlight_samba_mvt3_eerie_hotline_v7_contact.jpg")

T = 0.20  # transition duration in seconds (12 frames @ 60fps)

# 12 Segments across 52.00s (24 bars @ 112 BPM: 2 bars = 4.286s):
segments = [
    # 0: BARS 1-2 (0.00s - 4.286s, eff=4.286s)
    {"id": 0, "src": VIDEO_DRONE, "in": 12.0, "eff": 4.286, "type": "small_world_twilight", "speed": 1.0},

    # 1: BARS 3-4 (4.286s - 8.571s, eff=4.286s)
    {"id": 1, "src": VIDEO_5127, "in": 2.0, "eff": 4.286, "type": "highway_golden_stabilized", "speed": 1.0},

    # 2: BARS 5-6 (8.571s - 12.857s, eff=4.286s)
    {"id": 2, "src": None, "in": 0.0, "eff": 4.286, "type": "split_hotline_amber", "speed": 1.0},

    # 3: BARS 7-8 (12.857s - 17.143s, eff=4.286s)
    {"id": 3, "src": VIDEO_DRONE, "in": 35.0, "eff": 4.286, "type": "city_predrop_heat", "speed": 1.0},

    # [17.143s: BAR 9 BEAT 1 TUTTI DROP - 3-FRAME PLANAR BGW STROBE EXPLOSION]

    # 4: BARS 9-10 (17.143s - 21.429s, eff=4.286s)
    {"id": 4, "src": VIDEO_5128, "in": 5.0, "eff": 4.286, "type": "highway_breach_stabilized", "speed": 1.0},

    # 5: BARS 11-12 (21.429s - 25.714s, eff=4.286s)
    # [THE PORTAL CAR & HITCHCOCK ZOLLY]
    {"id": 5, "src": None, "in": 0.0, "eff": 4.286, "type": "portal_car_zolly", "speed": 1.0},

    # 6: BARS 13-14 (25.714s - 30.000s, eff=4.286s)
    # [THE HERO CROWS & VINYL SCRATCH TRANSITION]
    {"id": 6, "src": VIDEO_CROWS, "in": 12.0, "eff": 4.286, "type": "hero_crows_blooddusk", "speed": 1.0},

    # [30.000s: BAR 15 BEAT 1 INSTANT TRACK DROP]

    # 7: BARS 15-16 (30.000s - 34.286s, eff=4.286s)
    # [THE INSTANT TRACK DROP / HYPERSPEED BLAST]
    {"id": 7, "src": VIDEO_DRONE, "in": 65.0, "eff": 4.286, "type": "city_hyperspeed_blast", "speed": 8.0},

    # 8: BARS 17-18 (34.286s - 38.571s, eff=4.286s)
    # [TACTICAL SPLIT 2: PERCUSSION BREAKDOWN]
    {"id": 8, "src": None, "in": 0.0, "eff": 4.286, "type": "split_hotline_cyan", "speed": 1.0},

    # 9: BARS 19-20 (38.571s - 42.857s, eff=4.286s)
    # [PROTAGONIST: INTERSECTION HYPERLAPSE]
    {"id": 9, "src": VIDEO_DRONE, "in": 110.0, "eff": 4.286, "type": "city_hyperlapse_twilight", "speed": 5.0},

    # 10: BARS 21-22 (42.857s - 47.143s, eff=4.286s)
    # [ANTAGONIST: FINAL SPRINT]
    {"id": 10, "src": VIDEO_5128, "in": 22.0, "eff": 4.286, "type": "highway_finalsprint_stabilized", "speed": 1.0},

    # 11: BARS 23-24 (47.143s - 52.000s, eff=4.857s)
    # [CLIMAX CONVERGENCE & TUTTI CHOKE]
    {"id": 11, "src": VIDEO_5128, "in": 31.0, "eff": 4.857, "type": "highway_cadence_climax", "speed": 1.0},
]

print("=== [STAGE 1] Rendering Sub-Clips (Stabilized Motion, Portal Zolly & Hero Crows) ===")

clip_files = []

for seg in segments:
    idx = seg["id"]
    stype = seg["type"]
    eff = seg["eff"]
    dur = eff + (0.0 if idx == len(segments) - 1 else T)
    nframes = int(dur * 60)
    speed = seg["speed"]
    clip_path = os.path.join(OUTPUT_DIR, f"seg_v7_{idx:02d}.mp4")
    clip_files.append(clip_path)

    if os.path.exists(clip_path) and os.path.getsize(clip_path) > 100000:
        print(f"--> Segment {idx:02d} ({stype}) already rendered ({os.path.getsize(clip_path)/(1024*1024):.2f} MB), skipping.")
        continue

    print(f"--> Rendering segment {idx:02d} ({stype}, dur={dur:.2f}s)...")

    if stype == "small_world_twilight":
        # Conformal Stereographic Globe with 2560x2560 projection: 100% borderless full 16:9 orbital rotation
        fc = (
            f"[0:v]trim=start=0:end={dur:.3f},setpts=PTS-STARTPTS,fps=60,"
            f"scale=1920:1080,split[a][b];"
            f"[b]hflip[bf];"
            f"[a][bf]hstack,scale=3840:1920,"
            f"v360=input=e:output=sg:pitch=-90:h_fov=220:v_fov=220:w=2560:h=2560,"
            f"rotate='0.06*t*PI':ow=2560:oh=2560,"
            f"crop=1920:1080:(2560-1920)/2:(2560-1080)/2,"
            f"colorbalance=rs=-0.06:gs=-0.10:bs=0.22:rm=0.10:gm=-0.05:bm=-0.06:rh=0.30:gh=-0.02:bh=-0.14,"
            f"curves=all='0/0 0.20/0.14 0.50/0.50 0.80/0.88 1/0.98',"
            f"eq=saturation=1.35:contrast=1.28,"
            f"fps=60,settb=1/60,format=yuv420p[vout]"
        )
        cmd = [
            FFMPEG, "-y",
            "-ss", f"{seg['in']:.3f}", "-i", seg["src"],
            "-filter_complex", fc,
            "-map", "[vout]",
            "-t", f"{dur:.3f}",
            "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
            clip_path
        ]

    elif stype == "split_hotline_amber":
        # Top: Grand Ave Commercial crossroads (41.mov)
        # Bottom: Stabilized Highway 54 low asphalt (IMG_5127)
        trf_file = os.path.join(TRF_DIR, f"stab_seg_{idx:02d}.trf").replace("\\", "/")
        if not os.path.exists(trf_file):
            cmd_d = [
                FFMPEG, "-y", "-ss", "6.0", "-i", VIDEO_5127, "-t", f"{dur:.3f}",
                "-vf", f"crop=2400:1350:720:0,scale=1920:1080,vidstabdetect=stepsize=4:shakiness=8:accuracy=15:result={trf_file}",
                "-f", "null", "-"
            ]
            subprocess.run(cmd_d, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        fc = (
            f"[0:v]trim=start=0:end={dur:.3f},setpts=PTS-STARTPTS,fps=60,"
            f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:540:0:180,"
            f"colorbalance=rs=-0.06:gs=-0.08:bs=0.20:rm=0.12:gm=0.02:bm=-0.08:rh=0.32:gh=0.08:bh=-0.16,"
            f"eq=saturation=1.40:contrast=1.25[top];"
            f"[1:v]trim=start=0:end={dur:.3f},setpts=PTS-STARTPTS,fps=60,"
            f"crop=2400:1350:720:0,scale=1920:1080,"
            f"vidstabtransform=input={trf_file}:smoothing=30:optzoom=1:zoom=2:interpol=bicubic,"
            f"crop=1920:540:0:450,"
            f"colorbalance=rs=-0.08:gs=-0.12:bs=0.22:rm=0.15:gm=-0.02:bm=-0.10:rh=0.35:gh=0.04:bh=-0.18,"
            f"eq=saturation=1.45:contrast=1.30[bot];"
            f"[top][bot]vstack[stacked];"
            f"color=c=0xFF3300@0.45:s=1920x16,format=rgba[glow];"
            f"color=c=0xFF6600@0.85:s=1920x8,format=rgba[beam];"
            f"color=c=white@1.0:s=1920x2,format=rgba[core];"
            f"[stacked][glow]overlay=0:532:format=auto[v1];"
            f"[v1][beam]overlay=0:536:format=auto[v2];"
            f"[v2][core]overlay=0:539:format=auto,"
            f"fps=60,settb=1/60,format=yuv420p[vout]"
        )
        cmd = [
            FFMPEG, "-y",
            "-ss", "45.0", "-i", VIDEO_DRONE,
            "-ss", "6.0", "-i", VIDEO_5127,
            "-filter_complex", fc,
            "-map", "[vout]",
            "-t", f"{dur:.3f}",
            "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
            clip_path
        ]

    elif stype == "city_predrop_heat":
        # Protagonist pre-drop dive: Celluloid thermal bleed & 112 BPM rhythmic exposure breathing
        fc = (
            f"[0:v]trim=start=0:end={dur:.3f},setpts=PTS-STARTPTS,fps=60,"
            f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
            f"colorbalance=rs=-0.04:gs=-0.08:bs=0.24:rm=0.18:gm=0.04:bm=-0.12:rh=0.40:gh=0.10:bh=-0.22,"
            f"curves=all='0/0 0.18/0.14 0.50/0.52 0.82/0.92 1/1.0',"
            f"eq=eval=frame:contrast='1.25+0.12*sin(2*PI*t*1.867)':saturation=1.45,"
            f"fps=60,settb=1/60,format=yuv420p[vout]"
        )
        cmd = [
            FFMPEG, "-y",
            "-ss", f"{seg['in']:.3f}", "-i", seg["src"],
            "-filter_complex", fc,
            "-map", "[vout]",
            "-t", f"{dur:.3f}",
            "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
            clip_path
        ]

    elif stype == "portal_car_zolly":
        # Seg 05: The Portal Car & Hitchcock Zolly
        # Foreground: Turning car at Grand Ave intersection (41.mov at 44.0s)
        # Background: Stabilized Highway 54 dusk asphalt (IMG_5128 at 14.0s)
        trf_file = os.path.join(TRF_DIR, f"stab_seg_{idx:02d}.trf").replace("\\", "/")
        if not os.path.exists(trf_file):
            cmd_d = [
                FFMPEG, "-y", "-ss", "14.0", "-i", VIDEO_5128, "-t", f"{dur:.3f}",
                "-vf", f"crop=2400:1350:720:0,scale=1920:1080,vidstabdetect=stepsize=4:shakiness=8:accuracy=15:result={trf_file}",
                "-f", "null", "-"
            ]
            subprocess.run(cmd_d, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # F-curve contra-zoom: tight 2.2x zoom pulls back rapidly to 1.1x as car moves
        # Feathered elliptical alpha portal around the vehicle
        fc = (
            f"[1:v]trim=start=0:end={dur:.3f},setpts=PTS-STARTPTS,fps=60,"
            f"crop=2400:1350:720:0,scale=1920:1080,"
            f"vidstabtransform=input={trf_file}:smoothing=30:optzoom=1:zoom=2:interpol=bicubic,"
            f"colorbalance=rs=-0.08:gs=-0.12:bs=0.22:rm=0.14:gm=-0.02:bm=-0.08:rh=0.32:gh=0.05:bh=-0.16,"
            f"eq=saturation=1.40:contrast=1.28[bg];"
            f"[0:v]trim=start=0:end={dur:.3f},setpts=PTS-STARTPTS,fps=60,"
            f"scale=3840:2160,crop=1920:1080:960:540,"
            f"zoompan=z='if(lt(on,45),2.20-1.00*(1-pow(1-(on/45),3)),1.20)':x='(iw-iw/zoom)*0.5':y='(ih-ih/zoom)*0.55':d=1:s=1920x1080:fps=60,"
            f"colorbalance=rs=0.10:gs=-0.02:bs=-0.10:rm=0.22:gm=0.05:bm=-0.12:rh=0.38:gh=0.12:bh=-0.20,"
            f"eq=saturation=1.50:contrast=1.35,format=rgba,"
            f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lt(hypot((X-960)*0.75,Y-540),230),255,if(lt(hypot((X-960)*0.75,Y-540),460),255*(1-(hypot((X-960)*0.75,Y-540)-230)/230),0))'[car_portal];"
            f"[bg][car_portal]overlay=0:0:format=auto,"
            f"fps=60,settb=1/60,format=yuv420p[vout]"
        )
        cmd = [
            FFMPEG, "-y",
            "-ss", "44.0", "-i", VIDEO_DRONE,
            "-ss", "14.0", "-i", VIDEO_5128,
            "-filter_complex", fc,
            "-map", "[vout]",
            "-t", f"{dur:.3f}",
            "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
            clip_path
        ]

    elif stype == "hero_crows_blooddusk":
        # Seg 06: The Hero Crows & Vinyl Scratch Transition
        # High-contrast blood-dusk / twilight luma-split grade on the slow-mo centered crows
        # At tail (last 0.54s, Bar 14 Beat 4): Chromatic strobe flash anticipator
        fc = (
            f"[0:v]trim=start=0:end={dur:.3f},setpts=PTS-STARTPTS,fps=60,"
            f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
            f"colorbalance=rs=0.16:gs=-0.04:bs=-0.12:rm=0.24:gm=0.04:bm=-0.16:rh=0.42:gh=0.12:bh=-0.26,"
            f"curves=all='0/0 0.22/0.10 0.50/0.46 0.78/0.92 1/0.98',"
            f"eq=eval=frame:brightness='if(gte(t,{eff-0.54:.2f}),0.25*sin(2*PI*(t-{eff-0.54:.2f})*8),0)':contrast='if(gte(t,{eff-0.54:.2f}),1.65,1.35)':saturation=1.45,"
            f"fps=60,settb=1/60,format=yuv420p[vout]"
        )
        cmd = [
            FFMPEG, "-y",
            "-ss", f"{seg['in']:.3f}", "-i", seg["src"],
            "-filter_complex", fc,
            "-map", "[vout]",
            "-t", f"{dur:.3f}",
            "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
            clip_path
        ]

    elif stype == "city_hyperspeed_blast":
        # Seg 07: The Instant Track Drop / Hyperspeed Blast
        # 8x motion-smeared intersection rush surging forward as tutti drops
        fc = (
            f"[0:v]trim=start=0:end={dur*speed:.3f},setpts=0.125*PTS,fps=60,"
            f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
            f"tblend=all_mode=average,"
            f"colorbalance=rs=-0.06:gs=-0.08:bs=0.24:rm=0.16:gm=0.02:bm=-0.10:rh=0.38:gh=0.08:bh=-0.20,"
            f"eq=saturation=1.55:contrast=1.35,"
            f"fps=60,settb=1/60,format=yuv420p[vout]"
        )
        cmd = [
            FFMPEG, "-y",
            "-ss", f"{seg['in']:.3f}", "-i", seg["src"],
            "-filter_complex", fc,
            "-map", "[vout]",
            "-t", f"{dur:.3f}",
            "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
            clip_path
        ]

    elif stype == "split_hotline_cyan":
        # Seg 08: Tactical Split 2 (Percussion Breakdown)
        # Top: Grand Ave arterial (41.mov)
        # Bottom: Stabilized Highway 54 dusk curve (IMG_5128)
        trf_file = os.path.join(TRF_DIR, f"stab_seg_{idx:02d}.trf").replace("\\", "/")
        if not os.path.exists(trf_file):
            cmd_d = [
                FFMPEG, "-y", "-ss", "16.0", "-i", VIDEO_5128, "-t", f"{dur:.3f}",
                "-vf", f"crop=2400:1350:720:0,scale=1920:1080,vidstabdetect=stepsize=4:shakiness=8:accuracy=15:result={trf_file}",
                "-f", "null", "-"
            ]
            subprocess.run(cmd_d, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        fc = (
            f"[0:v]trim=start=0:end={dur:.3f},setpts=PTS-STARTPTS,fps=60,"
            f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:540:0:300,"
            f"colorbalance=rs=-0.08:gs=0.06:bs=0.22:rm=-0.04:gm=0.10:bm=0.14:rh=0.08:gh=0.15:bh=0.25,"
            f"eq=saturation=1.40:contrast=1.25[top];"
            f"[1:v]trim=start=0:end={dur:.3f},setpts=PTS-STARTPTS,fps=60,"
            f"crop=2400:1350:720:0,scale=1920:1080,"
            f"vidstabtransform=input={trf_file}:smoothing=30:optzoom=1:zoom=2:interpol=bicubic,"
            f"crop=1920:540:0:450,"
            f"colorbalance=rs=-0.10:gs=-0.05:bs=0.25:rm=0.08:gm=-0.02:bm=-0.05:rh=0.28:gh=0.05:bh=-0.12,"
            f"eq=saturation=1.45:contrast=1.30[bot];"
            f"[top][bot]vstack[stacked];"
            f"color=c=0x0099FF@0.45:s=1920x16,format=rgba[glow];"
            f"color=c=0x00E5FF@0.85:s=1920x8,format=rgba[beam];"
            f"color=c=white@1.0:s=1920x2,format=rgba[core];"
            f"[stacked][glow]overlay=0:532:format=auto[v1];"
            f"[v1][beam]overlay=0:536:format=auto[v2];"
            f"[v2][core]overlay=0:539:format=auto,"
            f"fps=60,settb=1/60,format=yuv420p[vout]"
        )
        cmd = [
            FFMPEG, "-y",
            "-ss", "85.0", "-i", VIDEO_DRONE,
            "-ss", "16.0", "-i", VIDEO_5128,
            "-filter_complex", fc,
            "-map", "[vout]",
            "-t", f"{dur:.3f}",
            "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
            clip_path
        ]

    elif stype == "city_hyperlapse_twilight":
        # 5x kinetic drone hyperlapse
        fc = (
            f"[0:v]trim=start=0:end={dur*speed:.3f},setpts=0.20*PTS,fps=60,"
            f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
            f"colorbalance=rs=-0.05:gs=-0.08:bs=0.24:rm=0.14:gm=0.02:bm=-0.10:rh=0.35:gh=0.06:bh=-0.18,"
            f"eq=saturation=1.50:contrast=1.30,"
            f"fps=60,settb=1/60,format=yuv420p[vout]"
        )
        cmd = [
            FFMPEG, "-y",
            "-ss", f"{seg['in']:.3f}", "-i", seg["src"],
            "-filter_complex", fc,
            "-map", "[vout]",
            "-t", f"{dur:.3f}",
            "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
            clip_path
        ]

    else:
        # Standard stabilized highway clips (1, 4, 10, 11)
        trf_file = os.path.join(TRF_DIR, f"stab_seg_{idx:02d}.trf").replace("\\", "/")
        if not os.path.exists(trf_file):
            cmd_d = [
                FFMPEG, "-y", "-ss", f"{seg['in']:.3f}", "-i", seg["src"], "-t", f"{dur:.3f}",
                "-vf", f"crop=2400:1350:720:0,scale=1920:1080,vidstabdetect=stepsize=4:shakiness=8:accuracy=15:result={trf_file}",
                "-f", "null", "-"
            ]
            subprocess.run(cmd_d, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        fc = (
            f"[0:v]trim=start=0:end={dur:.3f},setpts=PTS-STARTPTS,fps=60,"
            f"crop=2400:1350:720:0,scale=1920:1080,"
            f"vidstabtransform=input={trf_file}:smoothing=30:optzoom=1:zoom=2:interpol=bicubic,"
            f"colorbalance=rs=-0.08:gs=-0.12:bs=0.22:rm=0.16:gm=-0.02:bm=-0.08:rh=0.36:gh=0.05:bh=-0.16,"
            f"curves=all='0/0 0.20/0.14 0.50/0.48 0.80/0.88 1/0.98',"
            f"eq=saturation=1.45:contrast=1.30,"
            f"fps=60,settb=1/60,format=yuv420p[vout]"
        )
        cmd = [
            FFMPEG, "-y",
            "-ss", f"{seg['in']:.3f}", "-i", seg["src"],
            "-filter_complex", fc,
            "-map", "[vout]",
            "-t", f"{dur:.3f}",
            "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
            clip_path
        ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] Segment {idx} failed:\n{res.stderr[-1500:]}")
        sys.exit(1)
    print(f"[OK] Segment {idx:02d} rendered.")

print("\n[OK] All 12 sub-clips successfully rendered!")

# ==============================================================================
# STAGE 2: Master Assembly via Hardware xfade with Vinyl Scratch & Instant Drop
# ==============================================================================
print("\n=== [STAGE 2] Master Assembly via Hardware xfade with Vinyl Scratch & Instant Drop ===")

inputs = []
for cpath in clip_files:
    inputs.extend(["-i", cpath])

audio_idx = len(clip_files)
inputs.extend(["-i", AUDIO_PATH])

scratch_idx = audio_idx + 1
inputs.extend(["-i", SCRATCH_SFX])

# 11 beat-locked transitions between 12 clips:
# Transition 3 at 17.143s: TUTTI DROP (3-Frame Planar BGW Strobe)
# Transition 6 at 30.000s: INSTANT TRACK DROP (3-Frame Planar Chromatic Strobe into Hyperspeed Blast!)
transitions = [
    "wipeleft",   # 0 -> 1: Kinetic wipe into Highway Golden
    "horzopen",   # 1 -> 2: Horizontal split reveal for Hotline Miami Split 1
    "dissolve",   # 2 -> 3: Dissolve into Pre-Drop Heat Bleed
    "custom",     # 3 -> 4 [17.143s TUTTI DROP]: 3-FRAME PLANAR BGW STROBE EXPLOSION!
    "wipetl",     # 4 -> 5: Diagonal snap into The Portal Car & Zolly
    "slideleft",  # 5 -> 6: Fast slide into THE HERO CROWS
    "custom",     # 6 -> 7 [30.000s INSTANT TRACK DROP]: 3-FRAME CHROMATIC STROBE ON NEEDLE SCRATCH!
    "vertopen",   # 7 -> 8: Vertical split reveal for Hotline Miami Split 2
    "hlwind",     # 8 -> 9: High-velocity wind dissolve into Hyperlapse Intersection
    "slideleft",  # 9 -> 10: Fast slide into Highway Final Sprint
    "wipetl",     # 10 -> 11: Diagonal snap into Final Cadence Climax
]

filter_chains = []
curr_stream = "0:v"
cum_offset = 0.0

for k, t_name in enumerate(transitions):
    next_stream = f"{k+1}:v"
    out_stream = f"x{k+1}"

    cum_offset += segments[k]["eff"]
    offset = cum_offset

    if k == 3 and t_name == "custom":
        # 17.143s Tutti Drop: Planar Black-Gray-White Strobe Flash
        expr = "if(eq(PLANE,0),if(lt(P,0.25),0,if(lt(P,0.50),128,if(lt(P,0.75),255,B))),if(lt(P,0.75),128,B))"
        trans_str = f"[{curr_stream}][{next_stream}]xfade=transition=custom:expr='{expr}':duration={T:.2f}:offset={offset:.2f}[{out_stream}]"
    elif k == 6 and t_name == "custom":
        # 30.000s Instant Track Drop: Chromatic Strobe / High-Energy White Flash on Needle Scratch
        expr = "if(lt(P,0.30),255,if(lt(P,0.60),0,B))"
        trans_str = f"[{curr_stream}][{next_stream}]xfade=transition=custom:expr='{expr}':duration={T:.2f}:offset={offset:.2f}[{out_stream}]"
    else:
        trans_str = f"[{curr_stream}][{next_stream}]xfade=transition={t_name}:duration={T:.2f}:offset={offset:.2f}[{out_stream}]"

    filter_chains.append(trans_str)
    curr_stream = out_stream

# Final video grading & rhythmic lens breathing
final_tx = (
    f"[{curr_stream}]"
    f"vignette=angle='PI/4.6+PI/45*sin(2*PI*t*1.867)':eval=frame:aspect=16/9,"
    f"eq=eval=frame:brightness='if(between(t,51.40,51.52),0.75,0)':contrast='if(between(t,51.40,51.52),2.2,1.0)',"
    f"fade=t=out:st=51.50:d=0.50:color=black[vout]"
)
filter_chains.append(final_tx)

# Audio Pipeline: Mix John's Presto Agitato full band master + Scratch SFX at Bar 14 Beat 4 (29.46s)
# Dip orchestra slightly during the 0.54s back-cue scrub, then explode back on the 30.00s downbeat!
scratch_delay_ms = 29464 # Exactly Bar 14 Beat 4
audio_chain = (
    f"[{audio_idx}:a]volume=eval=frame:volume='if(between(t,29.46,29.98),0.40,1.0)'[a_music];"
    f"[{scratch_idx}:a]adelay={scratch_delay_ms}|{scratch_delay_ms},volume=1.4[a_scratch];"
    f"[a_music][a_scratch]amix=inputs=2:duration=first:dropout_transition=0,"
    f"loudnorm=I=-16:TP=-1.5:LRA=11,atrim=0:52.0,afade=t=out:st=51.2:d=0.8[aout]"
)
filter_chains.append(audio_chain)

filter_complex_str = " ; ".join(filter_chains)

cmd_master = [
    FFMPEG, "-y",
    *inputs,
    "-filter_complex", filter_complex_str,
    "-map", "[vout]",
    "-map", "[aout]",
    "-c:v", "h264_nvenc", "-preset", "p7", "-cq", "18",
    "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
    "-t", "52.0",
    OUTPUT_MP4
]

print("--> Executing NVENC master assembly (v7 Opus Edit)...")
res = subprocess.run(cmd_master, capture_output=True, text=True)
if res.returncode != 0:
    print("[ERROR] FFmpeg master assembly failed:")
    print(res.stderr[-2500:])
    sys.exit(1)
print(f"[OK] Master render complete: {OUTPUT_MP4}")

# Generate 4x4 Contact sheet across full 52.0 seconds
contact_cmd = [
    FFMPEG, "-y",
    "-i", OUTPUT_MP4,
    "-vf", "select='not(mod(n,195))',scale=480:270,tile=4x4",
    "-frames:v", "1",
    "-update", "1",
    CONTACT_JPG
]
subprocess.run(contact_cmd, check=True)
print(f"[OK] 4x4 Contact sheet saved: {CONTACT_JPG}")

# Persist milestone to DuckDB
try:
    import duckdb
    con = duckdb.connect(r"C:\Users\John\.gemini\config\mind.duckdb")
    event_id = f"VID_SUNSET54_V7_OPUS_{int(os.path.getmtime(OUTPUT_MP4))}"
    norm_path = OUTPUT_MP4.replace("\\", "/")
    con.execute("""
        INSERT OR REPLACE INTO mind.main.video_events (event_id, video_path, timestamp_sec, event_type, scene_score, logged_at)
        VALUES (?, ?, 52.0, 'sunset54_v7_opus_complete', 1.0, CURRENT_TIMESTAMP);
    """, [event_id, norm_path])
    con.close()
    print(f"[OK] Telemetry persisted to mind.duckdb: {event_id}")
except Exception as e:
    print(f"[WARN] DuckDB log error: {e}")
