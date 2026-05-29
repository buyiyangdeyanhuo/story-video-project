"""
Generate narration + word-synced SRT using edge-tts SubMaker.
"""
import asyncio
import edge_tts

TEXT = """从前，有一个农夫，他每天都要在地里辛苦地干活。
有一天，农夫正在田里锄地，突然听见砰的一声！
他扭头一看，哎呀！一只大白兔撞在了树桩上！
兔子晕倒了，被农夫轻轻松松捡回了家。
哇！这也太幸运了吧？农夫心里乐开了花！
他想：既然兔子会自己撞上来，那我为什么还要辛苦种地呢？
于是，农夫扔掉锄头，一屁股坐在树桩旁边。
他等啊等啊，等了一天又一天。
春天过去了，夏天来了，秋天也过去了。
田里长满了杂草，庄稼全都枯死了。
可是兔子呢？再也没有出现过第二只！
农夫饿着肚子，看着荒废的田地，后悔极了。
他终于明白了：天上不会掉馅饼，不劳而获是不可能的呀！
守株待兔这个成语，就是告诉我们——
不要学那个农夫，成功要靠自己的努力才行！
故事出自《韩非子·五蠹》"""

async def main():
    communicate = edge_tts.Communicate(TEXT.strip(), 'zh-CN-YunxiaNeural', rate='+8%', pitch='+5Hz')
    sub = edge_tts.SubMaker()

    with open('narration_synced.mp3', 'wb') as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub.feed(chunk)
                print(f"  Word: offset={chunk.get('offset')} dur={chunk.get('duration')} text={chunk.get('text')}")

    # Generate SRT from SubMaker
    srt = sub.get_srt()
    print(f"\nGenerated SRT ({len(srt)} chars):")
    print(srt[:800])

    with open('subtitles_synced.srt', 'w', encoding='utf-8') as f:
        f.write(srt)

    print("\nDONE — saved narration_synced.mp3 + subtitles_synced.srt")

asyncio.run(main())
