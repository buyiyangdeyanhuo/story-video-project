import subprocess, os

FFMPEG = r"C:\Users\91392\.workbuddy\binaries\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
os.chdir(r"C:\Users\91392\WorkBuddy\2026-05-28-16-28-53\wangyangbulao")

# Build drawtext filters one char at a time for reliable positioning
# Using msyh.ttc (Microsoft YaHei) - definitely has Chinese glyphs
title_vf = (
    "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':"
    "text='亡  羊  补  牢':"
    "fontsize=120:fontcolor=0x4A2F1A:"
    "x=(w-text_w)/2:y=(h-text_h)/2-70,"
    
    "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':"
    "text='wáng yáng bǔ láo':"
    "fontsize=36:fontcolor=0x8A8070:"
    "x=(w-text_w)/2:y=(h-text_h)/2+70,"
    
    "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':"
    "text='成 语 故 事':"
    "fontsize=28:fontcolor=0xA09080:"
    "x=(w-text_w)/2:y=(h-text_h)/2+130"
)

# With title voice
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

result = subprocess.run(cmd, capture_output=True, text=True)
stderr = result.stderr
if 'No usable font' in stderr or 'Cannot find' in stderr:
    print("FONT NOT FOUND. Let me try alternatives...")
    # Print the relevant part
    for line in stderr.split('\n'):
        if 'font' in line.lower() or 'drawtext' in line.lower() or 'error' in line.lower():
            print(f"  {line.strip()}")
elif result.returncode != 0:
    print(f"FAILED with code {result.returncode}")
    print(stderr[-800:])
else:
    print("SUCCESS: title_card.mp4 generated")
    print(stderr[-200:])
