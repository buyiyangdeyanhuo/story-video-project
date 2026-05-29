import subprocess, os
os.chdir(r"C:\Users\91392\WorkBuddy\2026-05-28-16-28-53\wangyangbulao")
FFMPEG = r"C:\Users\91392\.workbuddy\binaries\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"

subprocess.run([
    FFMPEG, '-y', '-i', 'title_card.mp4', '-vframes', '1', 'frame_check.png'
], check=True, capture_output=True)
print("frame_check.png extracted")
print("File size:", os.path.getsize('frame_check.png'))
