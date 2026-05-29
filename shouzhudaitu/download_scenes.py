import requests
import sys

# NOTE: COS signed URLs have expired. Regenerate via buddy-cloud.py or use ImageGen fallback.
urls = {
    'scene1': 'https://vcg-prod-1258344699.cos.ap-guangzhou.tencentcos.cn/text_to_video/results/1379431822/84580c72-2c38-42af-8c23-22020a6095d3_1779952545.mp4?<SIGNED_PARAMS>',
    'scene2': 'https://vcg-prod-1258344699.cos.ap-guangzhou.tencentcos.cn/text_to_video/results/1379431822/811b7428-1e79-4b70-aa7a-72b1ec236f99_1779952545.mp4?<SIGNED_PARAMS>',
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for name, url in urls.items():
    print(f'Downloading {name}...')
    r = requests.get(url, headers=headers, timeout=120)
    with open(f'{name}.mp4', 'wb') as f:
        f.write(r.content)
    print(f'  {name}: {len(r.content)} bytes')

print('All done!')
