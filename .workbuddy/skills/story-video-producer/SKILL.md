---
name: story-video-producer
description: >
  Produces narrated story videos with multi-scene AI-generated visuals,
  children-friendly voiceover, and burned-in subtitles. Use when the user wants
  to create an animated story video (e.g., idiom stories, fairy tales, fables)
  with Chinese narration and on-screen subtitles. Triggers: "生成故事视频",
  "做一个成语故事", "制作带配音的视频", "生成儿童故事视频", "做动画故事".
agent_created: true
---

# Story Video Producer

Produces complete story videos by orchestrating AI video generation (buddy-cloud.py),
text-to-speech (edge-tts), and FFmpeg compositing. The pipeline generates separate
AI video clips for each story scene, loops them to match narration segments, then
concatenates everything with voiceover and subtitles burned in.

## Prerequisites

Before starting, verify the toolchain:

1. **buddy-cloud.py** at `F:/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/buddy-multimodal-generation/scripts/buddy-cloud.py`
2. **edge-tts** installed in Python venv (`pip install edge-tts`)
3. **FFmpeg** available (BtbN static build)
4. **Python venv** with `requests` installed

## Design Principles

1. **Multi-scene is non-negotiable.** Never loop a single short clip — each story beat
   deserves its own AI-generated video segment. For a typical idiom story, budget 5-6
   separate video jobs (3-5s each, then looped to 15-25s in compositing).
2. **Children's voice wins.** Default to `zh-CN-YunxiaNeural` (可爱男声) or
   `zh-CN-XiaoxiaoNeural` (活泼女声) with +8% rate and +5Hz pitch. Adult voices
   like `zh-CN-YunjianNeural` are fallbacks for formal/adult-oriented content.
3. **Auto-subtitles from TTS engine.** Always let edge-tts generate VTT subtitles
   with word-level timestamps. Never hand-estimate SRT timing — it will drift.
4. **Title card opens every video.** The first 3-5 seconds should display the idiom
   name (large, styled) + pinyin + "成语故事" label. Users need to know what they're
   watching immediately. **CRITICAL: Title card background MUST NOT be black** —
   use the same light/paper tone as the scene illustrations (e.g. `#F5F0E8` for
   cartoon style, `#F0EDE4` for ink-wash style). The title card should feel like
   page one of the visual story, not a separate dark screen.
5. **Fallback gracefully.** When the video API hits its daily quota, switch to
   ImageGen → static images → FFmpeg Ken Burns zoom effect. The pipeline must
   not break.

## Complete Workflow

### Step 0: Get Credentials

Use `connect_cloud_service` to obtain the API token. This is required for
buddy-cloud.py video generation.

Do NOT hardcode tokens — always call `connect_cloud_service` first.

### Step 1: Select Visual Style & Design Story Scenes

**First, pick a visual style** that matches the idiom's mood and characters.
See `references/visual_styles.md` for the full style guide. Quick reference:

| Idiom Type | Recommended Style | Key Prompt Keyword |
|------------|-------------------|-------------------|
| 神话/历史/大气 | 中国风水墨画 | `中国风水墨画风格，水墨晕染，留白构图` |
| 动物寓言/幽默 | 卡通绘本 | `卡通绘本风格，柔和色彩，圆润造型` |
| 民间故事/动作 | 皮影戏 | `皮影戏风格，皮质质感，暖黄背光` |
| 幼儿向/搞笑 | Q版动漫 | `Q版动漫风格，大头萌系，明亮鲜艳` |
| 唯美/文学 | 水彩绘本 | `水彩绘本风格，梦幻柔光，诗意` |

Break the story into **1 title card + 4-6 key visual moments** covering the full narrative arc:

| Scene | Purpose | Target Duration |
|-------|---------|----------------|
| Scene 0 | Title card (idiom name) | 3-5s |
| Scene 1 | Introduction/setup | ~15-20s |
| Scene 2 | Development | ~15-20s |
| Scene 3 | Key moment/climax | ~15-25s |
| Scene 4 | Climax/action | ~15-20s |
| Scene 5 | Resolution/ending | ~15-20s |

Write a detailed Chinese prompt for each scene. Rules:
- **Keep the same style keyword** across all 5 scenes for visual consistency
- Describe specific action, characters, and composition
- Add mood keywords (宁静的/紧张的/欢快的/震撼的)
- Avoid modern elements in classical idiom scenes
- Keep each prompt under 500 characters

**Example — 画龙点睛 scenes:**

```
Scene 1: 中国风水墨画风格，一位古代画师在寺庙墙壁前挥笔画出四条巨龙，
         龙身蜿蜒盘旋，围观百姓惊叹仰望，柔和日光，古朴典雅的场景

Scene 2: 中国风水墨画风格，寺庙前聚集了一大群人，男女老少仰头观看壁画，
         交头接耳议论纷纷，4K画质

Scene 3: 中国风水墨画风格，画师手持毛笔蘸墨，特写龙的眼睛部位，
         笔尖精准落下，墨色晕染，神圣庄严

Scene 4: 中国风水墨画风格，画龙点睛后神龙破壁而出，金光四射，
         龙身环绕庙宇，众人震撼跪拜，电闪雷鸣

Scene 5: 中国风水墨画风格，神龙飞向云端，遨游天际，
         俯瞰山河大地，霞光万道，意境深远
```

### Step 2: Generate Scene Videos

Use `buddy-cloud.py` with `--no-poll` flag. **Max 2 concurrent jobs.**

```bash
echo -n "<token>" | python buddy-cloud.py video "<prompt>" --token-stdin --no-poll
```

**Script path is F: drive, NOT C: drive.**

Submit in batches of 2. Save each `job_id` for polling.

**Fallback: when video API quota is exhausted** (daily limit reached), use `ImageGen` to generate static images for remaining scenes, then convert to video with Ken Burns zoom effect via FFmpeg:

```bash
ffmpeg -y -loop 1 -i scene.png -t DURATION \
  -vf "zoompan=z='min(zoom+0.001,1.3)':d=125:s=1920x1080" \
  -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p scene_clip.mp4
```

This creates a slow-zoom video clip from a still image, which can then be used in the same compositing pipeline.

Poll completion:
```bash
echo -n "<token>" | python buddy-cloud.py status "<job_id>" --type video --token-stdin
```

When status shows `succeeded`, extract the `result_url` from output.

Download with Python requests (COS 403 without browser UA):
```python
import requests
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
r = requests.get(result_url, headers=headers, timeout=120)
with open(f'scene{i}.mp4', 'wb') as f:
    f.write(r.content)
```

### Step 3: Write Narration Script & Generate Voiceover

Write a children-friendly script in lively conversational Chinese. Rules:
- Use short sentences (8-15 characters)
- Include exclamations, rhetorical questions, and sound effect cues
- Refer to what's on screen at each moment
- Total length ~60-110 seconds for a full story
- **Always cite the classical source** at the end (e.g., "故事出自《韩非子·五蠹》"). Look up authoritative classical texts — 成语 stories have well-documented origins in works like 韩非子, 庄子, 战国策, 史记, etc.

**Example — 画龙点睛 narration:**

```
从前有一位很厉害的大画家！他叫张僧繇。
有一天，他在寺庙的墙上画了四条大龙。
哇！这些龙画得可真像啊！可是...为什么它们都没有眼睛呢？
围观的人们都很好奇，纷纷问画家：为什么不画眼睛呢？
画家笑着说：如果点上眼睛，龙就会飞走啦！
大家都不相信，哪有这么神奇的事情？
于是画家拿起毛笔，沾满了墨汁...
看！他在一条龙的眼睛上轻轻一点！
轰隆隆——天空突然暗了下来，电闪雷鸣！
那条被点了眼睛的龙，居然真的从墙上飞了出来！
金光闪闪的巨龙盘旋在空中，所有人都惊呆了！
神龙飞向了天空，消失在云层之中。
从那以后啊，画龙点睛这个成语就流传了下来。
它告诉我们：关键的一笔，才是最重要的！
```

Use edge-tts. For children: `zh-CN-YunxiaNeural` (cute male), rate `+8%`, pitch `+5Hz`.

```python
import asyncio, edge_tts

async def gen_tts():
    tts = edge_tts.Communicate(
        TEXT,
        'zh-CN-YunxiaNeural',
        rate='+8%',
        pitch='+5Hz'
    )
    await tts.save('narration.mp3')

asyncio.run(gen_tts())
```

Voice reference — see `references/edge_tts_voices.md` for full catalog.

### Step 3: Generate Narration + Synced Subtitles

Use **edge-tts CLI to generate audio AND word-synced VTT subtitles in one pass** — this ensures frame-accurate sync. Do NOT estimate SRT timing by hand.

```bash
cd WORK_DIR && python -m edge_tts \
  -f script.txt \
  -v zh-CN-YunxiaNeural \
  --rate=+8% --pitch=+5Hz \
  --write-media narration.mp3 \
  --write-subtitles subtitles.vtt
```

Save the narration text to `script.txt` first. The output `subtitles.vtt` contains word-level timestamps from the TTS engine — perfectly synced with the audio.

**Voice selection**:
- Children's stories → `zh-CN-YunxiaNeural` (可爱男声 / Cute Boy) or `zh-CN-XiaoxiaoNeural` (活泼女声 / Lively Girl)
- Other voice options in `references/edge_tts_voices.md`

### Step 4: Subtitle Styling

The VTT from edge-tts already has correct timestamps. Apply styling via FFmpeg force_style:

```
FontName=Microsoft YaHei,FontSize=28
PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3
Alignment=2 (bottom-center), MarginV=50
```

### Step 5: Create Title Card

The first thing viewers see must be the idiom name. Create a 3-5 second title card
with FFmpeg drawtext before compositing the full video.

```bash
ffmpeg -y -f lavfi -i "color=c=0xF5F0E8:s=1920x1080:d=4:r=24" \
  -i "title_voice.mp3" \
  -vf "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':\
text='<IDIOM CHARS WITH SPACES>':\
fontsize=120:fontcolor=0x4A2F1A:\
x=(w-text_w)/2:y=(h-text_h)/2-70,\
drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':\
text='<PINYIN WITH SPACES>':\
fontsize=36:fontcolor=0x8A8070:\
x=(w-text_w)/2:y=(h-text_h)/2+70,\
drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':\
text='成 语 故 事':\
fontsize=28:fontcolor=0xA09080:\
x=(w-text_w)/2:y=(h-text_h)/2+130" \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 128k -shortest title_card.mp4
```

Style notes:
- Background: `0xF5F0E8` (paper color / 纸色，与淡色插画风格统一)
- Font: **`msyh.ttc` (微软雅黑)** — simkai/simfang may render Chinese as boxes on some FFmpeg builds; msyh is most reliable
- Title: 120px, dark brown `0x4A2F1A`, centered
- Pinyin: 36px, dim `0x8A8070`
- Label: 28px, muted `0xA09080`
- Duration: 4s
- **Important**: Generate `title_voice.mp3` first via edge-tts with just the idiom name, then use it as audio input for the title card

Then prepend this title card when concatenating scene clips (Step 6).

### Step 6: Composite Final Video with FFmpeg

Use Python to orchestrate FFmpeg in **three steps**:

**Step 6a: Loop each scene (including title card) to its target duration**

```python
scenes = [
    (0, 4, 'title_card.mp4'),    # title card
    (4, 22, 'scene1.mp4'),       # scene video clips
    (22, 40, 'scene2.mp4'),
    (40, 60, 'scene3.mp4'),
    (60, 80, 'scene4.mp4'),
    (80, 112, 'scene5.mp4'),
]

for i, (start, end, file) in enumerate(scenes):
    dur = end - start
    if file == 'title_card.mp4':
        # Title card already at correct duration, just copy
        cmd = [ffmpeg, '-y', '-i', file, '-c', 'copy', '-an', f'seg{i}.ts']
    else:
        # Scene video: loop to fill duration
        cmd = [
            ffmpeg, '-y', '-stream_loop', '-1', '-i', file,
            '-t', str(dur), '-c:v', 'libx264', '-preset', 'ultrafast',
            '-crf', '18', '-an', f'seg{i}.ts'
        ]
    subprocess.run(cmd, check=True)
```

**Step 6b: Concat all segments + overlay audio + subtitles**

```python
# Write concat file
with open('concat.txt', 'w') as f:
    for i in range(len(scenes)):
        f.write(f"file 'seg{i}.ts'\n")

# SRT path on Windows needs double-escaped colon
srt_path = 'C\\\\:/Users/91392/.../subtitles.srt'
vf = f"subtitles='{srt_path}'"

cmd = [
    ffmpeg, '-y',
    '-f', 'concat', '-safe', '0', '-i', 'concat.txt',
    '-i', 'narration.mp3',
    '-vf', vf,
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
    '-c:a', 'aac', '-b:a', '128k',
    '-shortest', '-movflags', '+faststart',
    'output_final.mp4'
]
subprocess.run(cmd, check=True)
```

**Step 6c: Cleanup temp files**

Remove `.ts` segments and `concat.txt`.

### Step 7: Deliver

Output is a single MP4 file (1080p, ~60-90MB). Format is compatible with:
- WeChat 视频号
- Douyin / TikTok
- General video platforms

## Known Issues

| Issue | Solution |
|-------|----------|
| COS download 403 | Python requests + browser User-Agent header. curl/PowerShell won't work. |
| FFmpeg subtitle path on Windows | Simplest: `cd` to work dir and use bare filename `subtitles='subtitles.vtt'`. Full paths with `\` get mangled by FFmpeg escape parsing. Even `C\\\\:/xxx` format can fail. Relative paths are most reliable. |
| moviepy 2.x broken APIs | Avoid entirely. Use FFmpeg subprocess. |
| Video job concurrency | Max 2 at a time; 429 error if exceeded |
| buddy-cloud.py path | Always F: drive, never C: drive |
| Video API daily limit | Fallback to ImageGen + FFmpeg zoompan for remaining scenes |
| ImageGen size parameter ignored | ImageGen generates at 1280x720 regardless of size="1920x1080". Use FFmpeg zoompan to scale up to 1080p. |
| FFmpeg concat with mixed codec profiles | concat `-c copy` fails silently when segments use different codec profiles (e.g. High vs Baseline). Solution: encode all clips to .ts with same settings, or do a two-pass approach — first concat video-only segments (all .ts, no audio), then add audio+subtitles in a second ffmpeg pass. |
| Audio sampling rate mismatch | narration.mp3 via edge-tts is 24000Hz mono. When combining with 44100Hz title card audio, ffmpeg may produce crackling. Solution: keep all intermediate clips video-only (`-an`), add narration as sole audio source in final step. |
| Chinese font rendering (boxes) | `simkai.ttf` and `simfang.ttf` may render Chinese characters as empty boxes (□□□□) on some FFmpeg/Windows builds. **Always use `msyh.ttc` (微软雅黑)** for both title card drawtext and subtitle force_style — it is the most reliable Chinese font across all Windows configurations. |

## Assets

- `references/edge_tts_voices.md` — Full Chinese voice catalog with use-case settings
- `references/visual_styles.md` — Idiom-to-style mapping, prompt templates, and decision tree
