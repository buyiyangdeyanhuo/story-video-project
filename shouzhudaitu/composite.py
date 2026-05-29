import subprocess, os

ffmpeg = "C:/Users/91392/.workbuddy/binaries/ffmpeg/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe"
cwd = "C:/Users/91392/WorkBuddy/2026-05-28-13-45-45/shouzhudaitu"
os.chdir(cwd)

# Scene durations (narration is 63 seconds total)
scenes = [
    (0, 12,  'scene1.mp4',  'video'),   # 农夫劳作
    (12, 24, 'scene2.mp4',  'video'),   # 兔子撞树
    (24, 38, 'scene3.png',  'image'),   # 捡到兔子惊喜
    (38, 52, 'scene4.png',  'image'),   # 坐等+田地荒芜
    (52, 63, 'scene5.png',  'image'),   # 后悔+教训
]

# Step 1: Create video clips from images with Ken Burns zoom effect
print("=== Step 1: Generating video clips ===")
for i, (start, end, file, ftype) in enumerate(scenes):
    dur = end - start
    if ftype == 'image':
        out = f'scene{i+1}_clip.mp4'
        # simpler zoompan that definitely works
        cmd = [
            ffmpeg, '-y', '-loop', '1', '-i', file,
            '-t', str(dur),
            '-vf', 'zoompan=z=\'min(zoom+0.001,1.3)\':d=125:s=1920x1080',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
            '-pix_fmt', 'yuv420p',
            out
        ]
        print(f'  Scene {i+1}: image -> {dur}s video clip')
        subprocess.run(cmd, check=True)
    else:
        print(f'  Scene {i+1}: using existing video ({dur}s)')

print("=== Step 2: Looping video clips to target duration ===")
seg_files = []
for i, (start, end, file, ftype) in enumerate(scenes):
    dur = end - start
    src = f'scene{i+1}_clip.mp4' if ftype == 'image' else file
    seg = f'seg{i}.ts'
    seg_files.append(seg)
    cmd = [
        ffmpeg, '-y', '-stream_loop', '-1', '-i', src,
        '-t', str(dur), '-c:v', 'libx264', '-preset', 'ultrafast',
        '-crf', '18', '-an', '-pix_fmt', 'yuv420p', seg
    ]
    print(f'  Looping scene {i+1} ({dur}s) -> {seg}')
    subprocess.run(cmd, check=True)

print("=== Step 3: Writing concat file ===")
with open('concat.txt', 'w') as f:
    for seg in seg_files:
        f.write(f"file '{seg}'\n")

print("=== Step 4: Concatenating + overlaying audio + subtitles ===")
srt_path = 'C\\\\:/Users/91392/WorkBuddy/2026-05-28-13-45-45/shouzhudaitu/subtitles.srt'
vf = f"subtitles='{srt_path}':force_style='FontName=STKaiti,FontSize=30,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,Alignment=2,MarginV=50'"
cmd = [
    ffmpeg, '-y',
    '-f', 'concat', '-safe', '0', '-i', 'concat.txt',
    '-i', 'narration.mp3',
    '-vf', vf,
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
    '-c:a', 'aac', '-b:a', '128k',
    '-shortest', '-movflags', '+faststart',
    'shouzhudaitu_kids.mp4'
]
subprocess.run(cmd, check=True)

print("=== Step 5: Cleanup temp files ===")
for seg in seg_files:
    try: os.remove(seg)
    except: pass
try: os.remove('concat.txt')
except: pass
for i in range(3):
    try: os.remove(f'scene{i+4}_clip.mp4')
    except: pass

print("=== DONE! Output: shouzhudaitu_kids.mp4 ===")
