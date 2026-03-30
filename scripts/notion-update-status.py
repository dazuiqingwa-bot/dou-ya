#!/usr/bin/env python3
"""
更新 Notion 错题库某条记录的掌握状态和下次复习日。

用法：
  python3 notion-update-status.py <page_id> <掌握状态> <下次复习日YYYY-MM-DD>

掌握状态合法值：未掌握 / 半掌握 / 已掌握

示例：
  python3 notion-update-status.py 329d76be-33b0-8054-9dda-fdd632b5dba8 已掌握 2026-04-03
"""

import sys
import json
import urllib.request
from pathlib import Path
from datetime import date

VALID_STATUSES = {"未掌握", "半掌握", "已掌握"}

def load_api_key():
    key_path = Path.home() / ".config" / "notion" / "api_key"
    return key_path.read_text().strip()

def notion_patch(page_id: str, props: dict, token: str):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = json.dumps({"properties": props}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    if len(sys.argv) != 4:
        print("用法: python3 notion-update-status.py <page_id> <掌握状态> <YYYY-MM-DD>")
        sys.exit(1)

    page_id, status, next_review = sys.argv[1], sys.argv[2], sys.argv[3]

    if status not in VALID_STATUSES:
        print(f"错误：掌握状态必须是 {VALID_STATUSES} 之一，收到：{status}")
        sys.exit(1)

    # 简单校验日期格式
    try:
        date.fromisoformat(next_review)
    except ValueError:
        print(f"错误：日期格式不对，应为 YYYY-MM-DD，收到：{next_review}")
        sys.exit(1)

    token = load_api_key()

    props = {
        "掌握状态": {"select": {"name": status}},
        "下次复习日": {"date": {"start": next_review}},
    }

    result = notion_patch(page_id, props, token)
    title = ""
    for prop in result.get("properties", {}).values():
        if prop.get("type") == "title":
            texts = prop.get("title", [])
            title = "".join(t.get("plain_text", "") for t in texts)
            break

    print(f"✅ 已更新：{title or page_id}")
    print(f"   掌握状态 → {status}")
    print(f"   下次复习日 → {next_review}")

if __name__ == "__main__":
    main()
