#!/usr/bin/env python3
import urllib.request, json, pathlib, datetime

token = pathlib.Path.home().joinpath('.config/notion/api_key').read_text().strip()
DB_ID = '329d76be33b0804e9db3d9ee9fde3429'

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

# 先查数据库结构
print('=== 查询数据库字段结构 ===')
db = notion_req('GET', f'/databases/{DB_ID}')
props = db.get('properties', {})
for name, info in props.items():
    ptype = info.get('type', '?')
    if ptype in ('select', 'multi_select'):
        opts = info.get(ptype, {}).get('options', [])
        opt_names = [o['name'] for o in opts]
        print(f'  [{ptype}] {name}: {opt_names}')
    else:
        print(f'  [{ptype}] {name}')
