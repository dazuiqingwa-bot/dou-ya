#!/usr/bin/env python3
import urllib.request, json, pathlib

token = pathlib.Path.home().joinpath('.config/notion/api_key').read_text().strip()
headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2025-09-03',
    'Content-Type': 'application/json',
}

# 搜索所有可访问内容
req = urllib.request.Request(
    'https://api.notion.com/v1/search',
    data=json.dumps({'page_size': 20}).encode(),
    headers=headers,
    method='POST'
)
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())

for item in data.get('results', []):
    obj = item.get('object')
    iid = item.get('id')
    if obj == 'database':
        title = ''.join(x.get('plain_text','') for x in item.get('title', []))
        print(f'[database] {title}  id={iid}')
    elif obj == 'page':
        props = item.get('properties', {})
        tp = props.get('title', props.get('Name', props.get('题目标题', {})))
        texts = tp.get('title', tp.get('rich_text', []))
        title = ''.join(x.get('plain_text','') for x in texts) or '(无标题)'
        print(f'[page]     {title}  id={iid}')
