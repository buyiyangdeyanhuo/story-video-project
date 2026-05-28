# edge-tts Chinese Voice Catalog

All zh-CN voices available via edge-tts as of 2026-05.

| ShortName | Gender | Personality | Notes |
|-----------|--------|-------------|-------|
| `zh-CN-XiaoxiaoNeural` | Female | Warm | Gentle, soothing |
| `zh-CN-XiaoyiNeural` | Female | Lively | Energetic, upbeat |
| `zh-CN-YunjianNeural` | Male | Passion | Dramatic, intense |
| `zh-CN-YunxiNeural` | Male | Lively, Sunshine | Friendly, bright |
| `zh-CN-YunxiaNeural` | Male | Cute | Best for children's content |
| `zh-CN-YunyangNeural` | Male | Professional, Reliable | News/formal style |
| `zh-CN-liaoning-XiaobeiNeural` | Female | Humorous | Northeastern dialect |
| `zh-CN-shaanxi-XiaoniNeural` | Female | Bright | Shaanxi dialect |

## Recommended Settings by Use Case

| Use Case | Voice | Rate | Pitch |
|----------|-------|------|-------|
| Children's story | YunxiaNeural | +8% | +5Hz |
| Documentary | YunjianNeural | -5% | -2Hz |
| News report | YunyangNeural | -3% | 0 |
| Casual vlog | XiaoyiNeural | +3% | 0 |
| Bedtime story | XiaoxiaoNeural | -10% | -3Hz |

## How to List All Voices

```python
import asyncio, edge_tts
async def main():
    voices = await edge_tts.list_voices()
    for v in voices:
        if 'zh' in v['Locale']:
            print(f"{v['ShortName']}: {v.get('VoiceTag',{}).get('VoicePersonalities',[])}")
asyncio.run(main())
```
