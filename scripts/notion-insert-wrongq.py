#!/usr/bin/env python3
"""
错题录入脚本 - 通用版
用法：python3 notion-insert-wrongq.py '<JSON>'

JSON 字段说明（所有字段均可选，有默认值）：
{
  "title": "题目标题",         # 必填
  "subject": "数学",           # 学科（数学/语文/物理/化学/生物/英语）
  "knowledge": ["知识点1"],    # 知识点列表
  "error_type": ["错误原因"],  # 错误原因列表
  "my_answer": "我的答案",     # 我的答案
  "correct_answer": "正确答案",
  "analysis": "错因分析",      # 解题思路
  "grade": "初二下",           # 年级
  "source": "课堂测验",        # 错题来源
  "question_type": "选择题",   # 题型
}
"""
import sys, json, urllib.request, pathlib

token = pathlib.Path.home().joinpath('.config/notion/api_key').read_text().strip()
DB_ID = '329d76be33b0804e9db3d9ee9fde3429'

headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2025-09-03',
    'Content-Type': 'application/json',
}

def rt(text):
    return [{"text": {"content": str(text)}}]

def ms(items):
    return [{"name": str(i)} for i in items] if items else []

# 读参数
if len(sys.argv) < 2:
    print("用法: python3 notion-insert-wrongq.py '<JSON>'", file=sys.stderr)
    sys.exit(1)

try:
    d = json.loads(sys.argv[1])
except json.JSONDecodeError as e:
    print(f"JSON 解析失败: {e}", file=sys.stderr)
    sys.exit(1)

title     = d.get('title', '未命名题目')
subject   = d.get('subject', '数学')
knowledge = d.get('knowledge', [])
error_type= d.get('error_type', [])
my_ans    = d.get('my_answer', '')
correct   = d.get('correct_answer', '')
analysis  = d.get('analysis', '')
grade     = d.get('grade', '初二下')
source    = d.get('source', '课堂练习')
qtype     = d.get('question_type', '综合题')

props = {
    "题目标题":   {"title": rt(title)},
    "学科":       {"select": {"name": subject}},
    "掌握状态":   {"select": {"name": "未掌握"}},
    "需要重做":   {"checkbox": True},
    "年级/阶段":  {"select": {"name": grade}},
    "错题来源":   {"select": {"name": source}},
    "题型":       {"select": {"name": qtype}},
}

if knowledge:
    props["知识点"] = {"multi_select": ms(knowledge)}
if error_type:
    props["错误原因"] = {"multi_select": ms(error_type)}
if my_ans:
    props["我的答案"] = {"rich_text": rt(my_ans)}
if correct:
    props["正确答案"] = {"rich_text": rt(correct)}
if analysis:
    props["解题思路"] = {"rich_text": rt(analysis)}

page = {"parent": {"database_id": DB_ID}, "properties": props}

req = urllib.request.Request(
    'https://api.notion.com/v1/pages',
    data=json.dumps(page).encode(),
    headers=headers, method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=15) as r:
        result = json.loads(r.read())
    print(f'写入成功')
    print(f'页面ID: {result["id"]}')
    print(f'URL: {result.get("url","?")}')
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'失败 {e.code}: {body}', file=sys.stderr)
    sys.exit(1)
