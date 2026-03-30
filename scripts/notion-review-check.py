#!/usr/bin/env python3
"""
每天定时执行：查询 Notion 错题总库中今天需要复习的题目
输出格式供 Learning Center 生成推送内容
"""
import urllib.request, json, pathlib
from datetime import date

token = pathlib.Path.home().joinpath('.config/notion/api_key').read_text().strip()
DB_ID = '329d76be33b0804e9db3d9ee9fde3429'
TODAY = date.today().isoformat()  # 格式: 2026-03-27

headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

# 查询今天需要复习的题（下次复习日 <= 今天，掌握状态不是"已掌握"）
query = {
    "filter": {
        "and": [
            {
                "property": "下次复习日",
                "date": {"on_or_before": TODAY}
            },
            {
                "property": "掌握状态",
                "select": {"does_not_equal": "已掌握"}
            }
        ]
    },
    "sorts": [
        {"property": "下次复习日", "direction": "ascending"}
    ],
    "page_size": 10
}

req = urllib.request.Request(
    f'https://api.notion.com/v1/databases/{DB_ID}/query',
    data=json.dumps(query).encode(),
    headers=headers, method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())

    results = data.get('results', [])
    if not results:
        print('今天没有需要复习的题目')
    else:
        print(f'今天需要复习 {len(results)} 道题：')
        for item in results:
            props = item.get('properties', {})
            title_texts = props.get('题目标题', {}).get('title', [])
            title = ''.join(x.get('plain_text','') for x in title_texts) or '(无标题)'
            subject = props.get('学科', {}).get('select', {})
            subject_name = subject.get('name', '?') if subject else '?'
            status = props.get('掌握状态', {}).get('select', {})
            status_name = status.get('name', '?') if status else '?'
            review_date = props.get('下次复习日', {}).get('date', {})
            review_day = review_date.get('start', '?') if review_date else '?'
            page_id = item.get('id', '')
            print(f'  [{subject_name}] {title}')
            print(f'    掌握状态: {status_name}  应复习日: {review_day}')
            print(f'    page_id: {page_id}')

except urllib.error.HTTPError as e:
    print(f'查询失败 {e.code}: {e.read().decode()}')
except Exception as e:
    print(f'错误: {e}')
