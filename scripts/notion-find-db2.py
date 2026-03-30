#!/usr/bin/env python3
import urllib.request, json, pathlib

token = pathlib.Path.home().joinpath('.config/notion/api_key').read_text().strip()
headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2025-09-03',
    'Content-Type': 'application/json',
}

def notion_req(method, path, body=None):
    req = urllib.request.Request(
        f'https://api.notion.com/v1{path}',
        data=json.dumps(body).encode() if body else None,
        headers=headers,
        method=method
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# 搜索 filter by database
req = urllib.request.Request(
    'https://api.notion.com/v1/search',
    data=json.dumps({'filter': {'value': 'database', 'property': 'object'}, 'page_size': 20}).encode(),
    headers=headers,
    method='POST'
)
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())

results = data.get('results', [])
print(f'找到 {len(results)} 个 database：')
for item in results:
    iid = item.get('id')
    title = ''.join(x.get('plain_text','') for x in item.get('title', []))
    print(f'  [database] {title or "(无标题)"}  id={iid}')

if not results:
    print('没有找到 database，尝试查看已知 page 的子块...')
    # 查 page 329d76be-33b0-8058-bf08-e0c35cd90e1f 的子块（无标题页，可能是容器）
    page_id = '329d76be-33b0-8058-bf08-e0c35cd90e1f'
    blocks = notion_req('GET', f'/blocks/{page_id}/children')
    for b in blocks.get('results', []):
        btype = b.get('type')
        bid = b.get('id')
        print(f'  block type={btype}  id={bid}')
