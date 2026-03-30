#!/usr/bin/env python3
"""
从 Telegram 会话读取最新待写入错题，直接写入 Notion。
字段结构已确认：
  [title] 题目标题
  [select] 学科: 数学/语文/物理/化学/生物/英语
  [multi_select] 知识点
  [select] 掌握状态: 未掌握/半掌握/已掌握
  [multi_select] 错误原因: 审题错误/计算失误/概念不清/公式不会/步骤不完整/粗心/时间不够/表达不规范
  [checkbox] 需要重做
  [select] 年级/阶段
  [select] 题型: 计算题/选择题/填空题/应用题/阅读理解/实验题/作文表达/综合题
  [select] 错题来源
  [rich_text] 我的答案
  [rich_text] 正确答案
  [rich_text] 解题思路
  [rich_text] 备注
  [created_time] 录入日期 (自动)
  [date] 下次复习日
  [date] 最后复习日
  [files] 原题图片
"""
import urllib.request, json, pathlib

token = pathlib.Path.home().joinpath('.config/notion/api_key').read_text().strip()
DB_ID = '329d76be33b0804e9db3d9ee9fde3429'
headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2025-09-03',
    'Content-Type': 'application/json',
}

def rt(text):
    return [{"text": {"content": text[:2000]}}]

# ── 待写入内容（从 Telegram 会话提取）──────────────────────────────
ENTRY = {
    "题目标题":  "物理未作答题（待补录）",     # ← 从 Telegram 补充
    "学科":      "物理",
    "知识点":    ["待补充"],
    "掌握状态":  "未掌握",
    "错误原因":  ["步骤不完整"],
    "需要重做":  True,
    "年级/阶段": "初二下",
    "题型":      "综合题",
    "错题来源":  "课堂测验",
    "我的答案":  "未作答（空白）",
    "正确答案":  "待补充",
    "解题思路":  "待补充",
}
# ─────────────────────────────────────────────────────────────────────

page = {
    "parent": {"database_id": DB_ID},
    "properties": {
        "题目标题":  {"title": rt(ENTRY["题目标题"])},
        "学科":      {"select": {"name": ENTRY["学科"]}},
        "知识点":    {"multi_select": [{"name": k} for k in ENTRY["知识点"]]},
        "掌握状态":  {"select": {"name": ENTRY["掌握状态"]}},
        "错误原因":  {"multi_select": [{"name": k} for k in ENTRY["错误原因"]]},
        "需要重做":  {"checkbox": ENTRY["需要重做"]},
        "年级/阶段": {"select": {"name": ENTRY["年级/阶段"]}},
        "题型":      {"select": {"name": ENTRY["题型"]}},
        "错题来源":  {"select": {"name": ENTRY["错题来源"]}},
        "我的答案":  {"rich_text": rt(ENTRY["我的答案"])},
        "正确答案":  {"rich_text": rt(ENTRY["正确答案"])},
        "解题思路":  {"rich_text": rt(ENTRY["解题思路"])},
    }
}

req = urllib.request.Request(
    'https://api.notion.com/v1/pages',
    data=json.dumps(page).encode(),
    headers=headers, method='POST'
)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        result = json.loads(r.read())
    print(f'写入成功！页面ID: {result["id"]}')
    print(f'URL: {result.get("url","?")}')
except urllib.error.HTTPError as e:
    print(f'失败 {e.code}: {e.read().decode()}')
