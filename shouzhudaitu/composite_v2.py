"""
Re-composite video with synced subtitles.
Scene timings based on actual subtitle timestamps.
"""
import subprocess
import os

FFMPEG = "C:/Users/91392/.workbuddy/binaries/ffmpeg/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe"
WORK = "C:/Users/91392/WorkBuddy/2026-05-28-13-45-45/shouzhudaitu"

# Scene durations derived from subtitle timestamps:
# Scene 1 "农夫劳作" → subtitle lines 1-3: 0.0 → 11.5s
# Scene 2 "兔子撞树桩" → subtitle lines 4-8: 11.5 → 22.4s  
# Scene 3 "捡到兔子惊喜" → subtitle lines 9-10: 22.4 → 32.0s
# Scene 4 "等兔子+荒芜" → subtitle lines 11-15: 32.0 → 46.2s
# Scene 5 "后悔+教训+出处" → subtitle lines 16-20: 46.2 → 65.8s

scenes = [
    ("scene1.mp4", 11.5, None),   # AI video
    ("scene2.mp4", 10.9, None),   # AI video
    (None, 9.6, "scene3.png"),          # Image -> Ken Burns
    (None, 14.2, "scene4.png"),         # Image -> Ken Burns
    (None, 19.6, "scene5.png"),         # Image -> Ken Burns
]

total = sum(d[1] for d in scenes)
print(f"Total target duration: {total:.1f}s")

segment_files = []
segment_idx = 0

# Process each scene
for i, (clip_file, duration, img_file) in enumerate(scenes):
    seg_file = os.path.join(WORK, f"seg{i}.ts")
    segment_files.append(seg_file)
    
    if clip_file:
        # Loop existing video to target duration
        src = os.path.join(WORK, clip_file)
        subprocess.run([
            FFMPEG, "-y",
            "-stream_loop", "-1", "-i", src,
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-an",
            "-f", "mpegts", seg_file
        ], check=True, capture_output=True)
        
    elif img_file:
        # Ken Burns slow zoom from static image
        src = os.path.join(WORK, img_file)
        subprocess.run([
            FFMPEG, "-y",
            "-loop", "1", "-i", src,
            "-t", str(duration),
            "-vf", "zoompan=z='min(zoom+0.001,1.3)':d=125:s=1920x1080",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-an",
            "-f", "mpegts", seg_file
        ], check=True, capture_output=True)
    
    print(f"  Scene {i+1}: {duration:.1f}s → {seg_file}")

# Concatenate all segments
concat_file = os.path.join(WORK, "concat_v2.txt")
with open(concat_file, "w") as f:
    for sf in segment_files:
        f.write(f"file '{sf}'\n")

concat_video = os.path.join(WORK, "concat_v2.ts")
subprocess.run([
    FFMPEG, "-y",
    "-f", "concat", "-safe", "0", "-i", concat_file,
    "-c", "copy",
    concat_video
], check=True, capture_output=True)

# Final compose: video + synced audio + SRT subtitles
audio = os.path.join(WORK, "narration_synced.mp3")
# FFmpeg on Windows needs C\:/path format for subtitles filter
srt_path_ffmpeg = "C\\:/Users/91392/WorkBuddy/2026-05-28-13-45-45/shouzhudaitu/subtitles_synced.vtt"
output = os.path.join(WORK, "shouzhudaitu_kids_v2.mp4").replace("\\", "/")

subprocess.run([
    FFMPEG, "-y",
    "-i", concat_video,
    "-i", audio,
    "-vf", f"subtitles='{srt_path_ffmpeg}':force_style='FontName=STKaiti,FontSize=30,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,Alignment=2,MarginV=50'",
    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
    "-c:a", "aac", "-b:a", "128k",
    "-shortest",
    "-movflags", "+faststart",
    output
], check=True)

size_mb = os.path.getsize(output) / (1024*1024)
print(f"\nDONE: {output} ({size_mb:.1f} MB)")
