#!/usr/bin/env python3
import urllib.request, json, pathlib

token = pathlib.Path.home().joinpath('.config/notion/api_key').read_text().strip()
DB_ID = '329d76be33b0804e9db3d9ee9fde3429'

headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2025-09-03',
    'Content-Type': 'application/json',
}

def rt(text):
    return [{"text": {"content": text}}]

page = {
    "parent": {"database_id": DB_ID},
    "properties": {
        "题目标题": {
            "title": rt("柏拉图勾股数证明题")
        },
        "学科": {"select": {"name": "数学"}},
        "知识点": {"multi_select": [
            {"name": "勾股定理"},
            {"name": "完全平方公式"},
            {"name": "代数证明"}
        ]},
        "掌握状态": {"select": {"name": "未掌握"}},
        "错误原因": {"multi_select": [
            {"name": "步骤不完整"},
            {"name": "表达不规范"}
        ]},
        "需要重做": {"checkbox": True},
        "年级/阶段": {"select": {"name": "初二"}},
        "题型": {"select": {"name": "综合题"}},
        "错题来源": {"select": {"name": "课堂测验"}},
        "我的答案": {"rich_text": rt("有作答但逻辑不完整，得0分，扣5分")},
        "正确答案": {"rich_text": rt("证明：a²=(2m)²=4m²，b²=(m²-1)²=m⁴-2m²+1，c²=(m²+1)²=m⁴+2m²+1。a²+b²=4m²+m⁴-2m²+1=m⁴+2m²+1=c²，故a、b、c为勾股数。取m=2：a=4，b=3，c=5。")},
        "解题思路": {"rich_text": rt(
            "【错因分析】\n"
            "错误分类：步骤不完整 + 表达不规范\n"
            "核心问题：知道要算什么，但不知道怎么写成代数证明格式。\n"
            "概念缺口：完全平方公式展开 + 代数恒等式的证明规范。\n\n"
            "【标准解题步骤】\n"
            "第1步：明确目标——证明 a²+b²=c²\n"
            "第2步：展开各项\n"
            "  a²=(2m)²=4m²\n"
            "  b²=(m²-1)²=m⁴-2m²+1\n"
            "  c²=(m²+1)²=m⁴+2m²+1\n"
            "第3步：验证等式\n"
            "  a²+b²=4m²+m⁴-2m²+1=m⁴+2m²+1=c² ✓\n"
            "第4步：举例\n"
            "  取m=2：a=4，b=3，c=5，3²+4²=25=5² ✓\n\n"
            "【针对性练习】\n"
            "练习1：若a=2n，b=n²-1，c=n²+1（n>1整数），证明a、b、c是勾股数，取n=3给出一组。\n"
            "练习2：验证哪组是勾股数：①3,4,5  ②5,12,13  ③6,8,10，并说明理由。\n"
            "练习3：计算(m²+1)²-(m²-1)²，化简结果，说明与(2m)²的关系。"
        )},
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
    print(f'写入成功！')
    print(f'页面ID: {result["id"]}')
    print(f'URL: {result.get("url","?")}')
except urllib.error.HTTPError as e:
    print(f'失败 {e.code}: {e.read().decode()}')
