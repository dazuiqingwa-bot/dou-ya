#!/usr/bin/env python3
import json
from pathlib import Path

MAIN = Path('/Users/dazuiqingwa/.openclaw/agents/main/sessions/sessions.json')
DOUYA = Path('/Users/dazuiqingwa/.openclaw/agents/douya/sessions/sessions.json')


def load(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def dump(path: Path, data):
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    main_data = load(MAIN)
    douya_data = load(DOUYA)

    # ASA · Telegram
    tg_key = 'agent:main:telegram:direct:8058767394'
    if tg_key in main_data:
        entry = main_data[tg_key]
        entry['displayName'] = 'ASA · Telegram'
        origin = entry.setdefault('origin', {})
        origin['label'] = 'ASA · Telegram'
        origin['from'] = 'telegram:8058767394'
        origin['to'] = 'telegram:8058767394'

    # ASA · Web
    web_key = 'agent:main:main'
    if web_key in main_data:
        entry = main_data[web_key]
        entry['displayName'] = 'ASA · Web'
        entry['label'] = 'ASA · Web'
        entry['channel'] = 'webchat'
        origin = entry.setdefault('origin', {})
        origin['provider'] = 'webchat'
        origin['surface'] = 'webchat'
        origin['chatType'] = 'direct'
        origin['label'] = 'ASA · Web'
        origin['from'] = 'webchat:openclaw-control-ui'
        origin['to'] = 'webchat:openclaw-control-ui'
        dc = entry.setdefault('deliveryContext', {})
        dc['channel'] = 'webchat'

    # ASA · Heartbeat
    hb_key = 'agent:main:heartbeat'
    if hb_key in main_data:
        entry = main_data[hb_key]
        entry['displayName'] = 'ASA · Heartbeat'
        entry['label'] = 'ASA · Heartbeat'
        origin = entry.setdefault('origin', {})
        origin['label'] = 'ASA · Heartbeat'
        origin['provider'] = 'heartbeat'
        origin['from'] = 'heartbeat'
        origin['to'] = 'heartbeat'

    # 豆芽 · Feishu
    fs_key = 'agent:douya:feishu:direct:ou_216a3f71ce740715ecb08de972fb0749'
    if fs_key in douya_data:
        entry = douya_data[fs_key]
        entry['displayName'] = '豆芽 · Feishu'
        entry['label'] = '豆芽 · Feishu'
        origin = entry.setdefault('origin', {})
        origin['label'] = '豆芽 · Feishu'

    # James Gao (Telegram slash session) → ASA · Telegram (slash)
    slash_key = 'agent:main:telegram:slash:8058767394'
    if slash_key in main_data:
        entry = main_data[slash_key]
        entry['displayName'] = 'ASA · Telegram (slash)'
        origin = entry.setdefault('origin', {})
        origin['label'] = 'ASA · Telegram (slash)'

    # 飞书 main agent session → 豆芽 · Feishu (main)
    fs_main_key = 'agent:main:feishu:direct:ou_216a3f71ce740715ecb08de972fb0749'
    if fs_main_key in main_data:
        entry = main_data[fs_main_key]
        entry['displayName'] = '豆芽 · Feishu (main)'
        origin = entry.setdefault('origin', {})
        origin['label'] = '豆芽 · Feishu (main)'

    dump(MAIN, main_data)
    dump(DOUYA, douya_data)
    print('Session names corrected.')
    print('Next step: openclaw gateway restart')


if __name__ == '__main__':
    main()
