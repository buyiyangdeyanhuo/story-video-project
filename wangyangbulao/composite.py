import subprocess, os

FFMPEG = r"C:\Users\91392\.workbuddy\binaries\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
os.chdir(r"C:\Users\91392\WorkBuddy\2026-05-28-16-28-53\wangyangbulao")

# ============================================================
# Scene timing from subtitles (~82s total narration)
# Scene 1 is "happy shepherd on hillside", Scene 2 is "hole in fence"
# Reuse scene1 for opening/closing, scene2 for middle crisis sections
# ============================================================
scenes = [
    (0,  'title_card.mp4', 4,   True),    # title card
    (1,  'scene1.png',     18,  False),   # ~23s: happy shepherd
    (2,  'scene2.png',     18,  False),   # ~41s: finding hole
    (3,  'scene2.png',     16,  False),   # ~57s: wolf at night
    (4,  'scene2.png',     18,  False),   # ~75s: counting sheep sad
    (5,  'scene1.png',     18,  False),   # ~93s: fixing pen, happy ending
]

print("=== Step 1: Creating video segments ===")
for idx, src, dur, is_video in scenes:
    seg = f'seg{idx}.ts'
    if is_video:
        cmd = [FFMPEG, '-y', '-i', src,
               '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
               '-an', seg]
    else:
        cmd = [FFMPEG, '-y', '-loop', '1', '-i', src,
               '-t', str(dur),
               '-vf', "zoompan=z='min(zoom+0.001\\,1.2)':d=125:s=1920x1080",
               '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
               '-an', seg]
    r = subprocess.run(cmd, capture_output=True, text=True)
    ok = r.returncode == 0
    if ok:
        print(f"  seg{idx}.ts: OK ({dur}s)")
    else:
        print(f"  seg{idx}.ts: FAILED")
        print(r.stderr[-300:])
        exit(1)

# Concat list
with open('concat.txt', 'w') as f:
    for i in range(len(scenes)):
        f.write(f"file 'seg{i}.ts'\n")

print("\n=== Step 2: Compositing final video ===")

cmd = [
    FFMPEG, '-y',
    '-f', 'concat', '-safe', '0', '-i', 'concat.txt',
    '-i', 'narration.mp3',
    '-vf', ("subtitles='subtitles.vtt':"
            "force_style='FontName=Microsoft YaHei,FontSize=28,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,"
            "Alignment=2,MarginV=50'"),
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
    '-c:a', 'aac', '-b:a', '128k',
    '-shortest', '-movflags', '+faststart',
    '亡羊补牢_成语故事.mp4'
]

r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("COMPOSITE FAILED!")
    print(r.stderr[-500:])
    exit(1)

print("SUCCESS! Output: 亡羊补牢_成语故事.mp4")

# Cleanup
for f in os.listdir('.'):
    if f.startswith('seg') and f.endswith('.ts'):
        os.remove(f)
if os.path.exists('concat.txt'):
    os.remove('concat.txt')
print("Cleaned temp files.")
