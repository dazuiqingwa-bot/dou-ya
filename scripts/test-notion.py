#!/usr/bin/env python3
import urllib.request, urllib.parse, json, pathlib

key = pathlib.Path.home() / '.config/notion/api_key'
token = key.read_text().strip()

req = urllib.request.Request(
    'https://api.notion.com/v1/search',
    data=json.dumps({'query': '禾禾', 'page_size': 10}).encode(),
    headers={
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json',
    },
    method='POST'
)

with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read())

results = data.get('results', [])
print(f'连通成功，共找到 {len(results)} 个结果：')
for r in results:
    obj = r.get('object', '?')
    if obj == 'database':
        name = ''.join(x.get('plain_text','') for x in r.get('title', []))
    else:
        props = r.get('properties', {})
        tp = props.get('title', props.get('Name', props.get('题目', {})))
        texts = tp.get('title', tp.get('rich_text', []))
        name = ''.join(x.get('plain_text','') for x in texts) or r.get('id','?')
    print(f'  [{obj}] {name}  id={r["id"]}')
