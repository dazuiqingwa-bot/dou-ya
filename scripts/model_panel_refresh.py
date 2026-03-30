#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/Users/gaojames/.openclaw/workspace')
CANVAS = ROOT / 'canvas'
OUT = CANVAS / 'model-panel-data.json'


def run(cmd, shell=False):
    try:
        if shell:
            text = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
        else:
            text = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        return {"ok": True, "text": text}
    except subprocess.CalledProcessError as e:
        return {"ok": False, "text": e.output, "code": e.returncode}
    except Exception as e:
        return {"ok": False, "text": str(e), "code": None}


def extract_json_blob(text):
    if not text:
        return None
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start:end+1]


def clean_model_list_text(text):
    keep = []
    started = False
    for ln in text.splitlines():
        if ln.startswith('Model'):
            started = True
        if started and ln.strip():
            keep.append(ln.rstrip())
    return '\n'.join(keep)


def parse_models_list(text):
    text = clean_model_list_text(text)
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        return []
    rows = []
    for ln in lines[1:]:
        parts = re.split(r'\s{2,}', ln.strip())
        if len(parts) < 6:
            continue
        model, input_types, ctx, local, auth, tags = parts[:6]
        rows.append({
            'id': model,
            'input': input_types,
            'context': ctx,
            'local': local == 'yes',
            'auth': auth == 'yes',
            'tags': [t.strip() for t in tags.split(',') if t.strip()],
            'status': 'missing' if 'missing' in tags else 'ok'
        })
    return rows


def parse_ollama_list(text):
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        return []
    rows = []
    for ln in lines[1:]:
        parts = re.split(r'\s{2,}', ln.strip())
        if len(parts) < 4:
            continue
        name, model_id, size, modified = parts[:4]
        rows.append({
            'name': name,
            'id': model_id,
            'size': size,
            'modified': modified,
        })
    return rows


CANVAS.mkdir(parents=True, exist_ok=True)

models_status = run(['openclaw', 'models', 'status', '--json'])
models_list = run('openclaw models list', shell=True)
version = run(['openclaw', '--version'])
health = run(['openclaw', 'health'])
ollama_bin = shutil.which('ollama')
ollama_list = run(['ollama', 'list']) if ollama_bin else {"ok": False, "text": 'ollama not installed'}

status_json = {}
status_blob = extract_json_blob(models_status['text']) if models_status.get('text') else None
if status_blob:
    try:
        status_json = json.loads(status_blob)
    except Exception:
        status_json = {'parseError': True, 'raw': models_status['text']}

list_rows = parse_models_list(models_list['text']) if models_list['ok'] else []
ollama_rows = parse_ollama_list(ollama_list['text']) if ollama_list['ok'] else []

provider_health = []
for item in (((status_json.get('auth') or {}).get('oauth') or {}).get('providers') or []):
    provider_health.append({
        'provider': item.get('provider'),
        'status': item.get('status'),
        'expiresAt': item.get('expiresAt'),
        'remainingMs': item.get('remainingMs'),
        'profiles': item.get('profiles', []),
    })

payload = {
    'generatedAt': datetime.now(timezone.utc).isoformat(),
    'panelVersion': 'v0.1',
    'gateway': {
        'openclawVersion': version['text'].strip() if version['ok'] else None,
        'healthText': health['text'].strip() if health['ok'] else None,
    },
    'status': {
        'defaultModel': status_json.get('defaultModel'),
        'resolvedDefault': status_json.get('resolvedDefault'),
        'fallbacks': status_json.get('fallbacks', []),
        'imageModel': status_json.get('imageModel'),
        'allowed': status_json.get('allowed', []),
        'aliases': status_json.get('aliases', {}),
    },
    'providers': provider_health,
    'catalog': list_rows,
    'local': {
        'ollamaInstalled': bool(ollama_bin),
        'ollamaBinary': ollama_bin,
        'ollamaModels': ollama_rows,
        'futureHosts': [
            {
                'name': 'Mac mini',
                'status': 'reserved',
                'note': '预留本地模型部署位：到货后接入 Ollama / OMLX / LM Studio 任选其一'
            }
        ]
    },
    'ops': {
        'switchExamples': [
            'openclaw models set openai-codex/gpt-5.4',
            'openclaw models set claude',
            'openclaw models set ollama/gpt-oss:20b'
        ],
        'authExamples': [
            'openclaw models auth login --provider openai-codex',
            'openclaw models auth paste-token --provider anthropic'
        ],
        'installExamples': [
            'ollama pull gpt-oss:20b',
            'ollama pull qwen2.5-coder:32b',
            'ollama pull deepseek-r1:32b'
        ],
        'refreshCommand': f'python3 {ROOT / "scripts" / "model_panel_refresh.py"}'
    },
    'raw': {
        'modelsStatusOk': models_status['ok'],
        'modelsListOk': models_list['ok'],
        'ollamaListOk': ollama_list['ok'],
        'modelsListText': models_list['text'],
        'ollamaListText': ollama_list['text'],
    }
}

OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
print(str(OUT))
