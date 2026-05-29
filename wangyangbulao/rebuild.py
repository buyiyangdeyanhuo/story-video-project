"""
Rebuild 亡羊补牢 title card with proper Chinese font (msyh.ttc)
and composite the full video.
"""
import subprocess, os, sys

FFMPEG = r"C:\Users\91392\.workbuddy\binaries\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
WORK_DIR = r"C:\Users\91392\WorkBuddy\2026-05-28-16-28-53\wangyangbulao"
os.chdir(WORK_DIR)

# ============================================================
# Step 1: Generate title card with msyh.ttc (Microsoft YaHei)
# Background: paper color #F5F0E8
# Title voice "亡羊补牢" already exists as title_voice.mp3
# ============================================================
print("=== Generating title card ===")

title_vf = (
    "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':"
    "text='亡':'fontsize=120:fontcolor=0x5B3A1A:"
    "x=(w-text_w)/2-180:y=(h-text_h)/2-60,"
    
    "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':"
    "text='羊':'fontsize=120:fontcolor=0x5B3A1A:"
    "x=(w-text_w)/2-60:y=(h-text_h)/2-60,"
    
    "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':"
    "text='补':'fontsize=120:fontcolor=0x5B3A1A:"
    "x=(w-text_w)/2+60:y=(h-text_h)/2-60,"
    
    "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':"
    "text='牢':'fontsize=120:fontcolor=0x5B3A1A:"
    "x=(w-text_w)/2+180:y=(h-text_h)/2-60,"
    
    "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':"
    "text='wáng yáng bǔ láo':fontsize=32:fontcolor=0x8A8070:"
    "x=(w-text_w)/2:y=(h-text_h)/2+70,"
    
    "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':"
    "text='成语故事 —— 《战国策》':fontsize=28:fontcolor=0xA09080:"
    "x=(w-text_w)/2:y=(h-text_h)/2+120"
)

# Check if title_voice.mp3 exists
title_audio_exists = os.path.exists("title_voice.mp3")

if title_audio_exists:
    cmd = [
        FFMPEG, '-y',
        '-f', 'lavfi', '-i', 'color=c=0xF5F0E8:s=1920x1080:d=4:r=24',
        '-i', 'title_voice.mp3',
        '-vf', title_vf,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k',
        '-shortest',
        'title_card.mp4'
    ]
else:
    cmd = [
        FFMPEG, '-y',
        '-f', 'lavfi', '-i', 'color=c=0xF5F0E8:s=1920x1080:d=4:r=24',
        '-vf', title_vf,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
        '-an',
        'title_card.mp4'
    ]

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stderr[-500:] if result.stderr else "OK")
if result.returncode != 0:
    print("Title card generation FAILED!")
    sys.exit(1)
print("Title card generated: title_card.mp4")

# ============================================================
# Step 2: Generate scene images (if not present)
# ============================================================
# Check if we need to regenerate scenes
existing_scenes = [f for f in os.listdir('.') if f.startswith('scene') and f.endswith('.png')]
if len(existing_scenes) < 6:
    print("\n=== Scene images missing, need regeneration ===")
    print(f"Found {len(existing_scenes)} scene images, need 6")
    print("Please run the image generation step first.")
    # We'll continue if scenes exist from a previous gen
else:
    print(f"\n=== Found {len(existing_scenes)} scene images ===")

# ============================================================
# Step 3: Create scene video clips with Ken Burns zoom
# ============================================================
print("\n=== Creating scene video clips ===")

# Scene timing from subtitles
scenes = [
    (0,  'title_card.mp4', 4,  True),    # title card 0-4s
    (1,  'scene1.png',     19, False),   # 4-23s
    (2,  'scene2.png',     19, False),   # 23-42s
    (3,  'scene3.png',     16, False),   # 42-58s
    (4,  'scene4.png',     19, False),   # 58-77s
    (5,  'scene5.png',     19, False),   # 77-96s
]

for idx, src, dur, is_video in scenes:
    seg_file = f'seg{idx}.ts'
    if is_video:
        # Title card: copy as-is
        subprocess.run([
            FFMPEG, '-y', '-i', src,
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
            '-an', seg_file
        ], check=True, capture_output=True)
        print(f"  seg{idx}.ts: title card -> {dur}s")
    else:
        if not os.path.exists(src):
            print(f"  WARNING: {src} not found, skipping seg{idx}")
            continue
        # Still image -> zoompan
        subprocess.run([
            FFMPEG, '-y', '-loop', '1', '-i', src,
            '-t', str(dur),
            '-vf', f"zoompan=z='min(zoom+0.001\\,1.25)':d=125:s=1920x1080",
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
            '-an', seg_file
        ], check=True, capture_output=True)
        print(f"  seg{idx}.ts: {src} -> {dur}s zoompan")

# ============================================================
# Step 4: Concat + audio + subtitles
# ============================================================
print("\n=== Compositing final video ===")

# Write concat file
existing_segs = [f'seg{i}.ts' for i in range(6) if os.path.exists(f'seg{i}.ts')]
if not existing_segs:
    print("ERROR: No segments generated!")
    sys.exit(1)

with open('concat.txt', 'w') as f:
    for seg in existing_segs:
        f.write(f"file '{seg}'\n")

# Use relative path for subtitles (most reliable on Windows)
sub_cmd = [
    FFMPEG, '-y',
    '-f', 'concat', '-safe', '0', '-i', 'concat.txt',
    '-i', 'narration.mp3',
    '-vf', "subtitles='subtitles.vtt':force_style='FontName=Microsoft YaHei,FontSize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,Alignment=2,MarginV=50'",
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
    '-c:a', 'aac', '-b:a', '128k',
    '-shortest', '-movflags', '+faststart',
    '亡羊补牢_成语故事_v2.mp4'
]

result = subprocess.run(sub_cmd, capture_output=True, text=True)
print(result.stderr[-500:] if result.stderr else "OK")
if result.returncode != 0:
    print("Compositing FAILED!")
    print(result.stderr)
    sys.exit(1)

print("\n=== Cleanup ===")
# Keep the v2 output
print("Done! Output: 亡羊补牢_成语故事_v2.mp4")
