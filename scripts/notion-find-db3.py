#!/usr/bin/env python3
import urllib.request, json, pathlib

token = pathlib.Path.home().joinpath('.config/notion/api_key').read_text().strip()
headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2025-09-03',
    'Content-Type': 'application/json',
}

def notion_req(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f'https://api.notion.com/v1{path}',
        data=data, headers=headers, method=method
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# 已知的 page ID，逐个查子块
page_ids = [
    ('329d76be-33b0-8054-9dda-fdd632b5dba8', '英语阅读推断题失分'),
    ('329d76be-33b0-808e-84db-d62550611e8a', '串并联电路电流判断错误'),
    ('329d76be-33b0-80e8-a77f-eb5ea2d02464', '一次函数图像判断错误'),
    ('329d76be-33b0-8058-bf08-e0c35cd90e1f', '无标题页'),
]

# 先看无标题页的父级，它可能是数据库的一行
for pid, name in page_ids[:1]:
    print(f'\n=== 查 {name} 的页面详情 ===')
    page = notion_req('GET', f'/pages/{pid}')
    parent = page.get('parent', {})
    print(f'parent type: {parent.get("type")}')
    print(f'parent id: {parent.get("database_id") or parent.get("page_id") or parent.get("block_id")}')
    props = page.get('properties', {})
    print(f'字段数量: {len(props)}')
    for k, v in list(props.items())[:5]:
        print(f'  字段: {k} ({v.get("type")})')
