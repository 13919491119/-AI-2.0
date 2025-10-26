#!/usr/bin/env python3
"""
Simple local model registry helper (filesystem-backed).
Usage examples:
  python3 tools/model_registry.py register artifacts/  # copy artifacts into registry and record index
"""
import os
import shutil
import json
import argparse
from datetime import datetime


REGISTRY_DIR = 'models/registry'
INDEX_FILE = os.path.join(REGISTRY_DIR, 'index.json')


def ensure():
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    if not os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)


def register(artifact_dir):
    ensure()
    # expect metadata.json inside artifact_dir
    meta = os.path.join(artifact_dir, 'metadata.json')
    if not os.path.exists(meta):
        raise SystemExit('metadata.json not found in artifact dir')
    with open(meta, 'r', encoding='utf-8') as f:
        m = json.load(f)
    version = m.get('sha256')
    target = os.path.join(REGISTRY_DIR, version)
    if os.path.exists(target):
        print('artifact already registered:', version)
        return version
    shutil.copytree(artifact_dir, target)
    # append index
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        idx = json.load(f)
    entry = {
        'version': version,
        'path': target,
        'registered_at': datetime.utcnow().isoformat() + 'Z',
        'metadata': m,
    }
    idx.append(entry)
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)
    print('registered', version)
    return version


def list_registry():
    ensure()
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        idx = json.load(f)
    for e in idx:
        print(e['version'], e['registered_at'])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['register', 'list'])
    p.add_argument('path', nargs='?')
    args = p.parse_args()
    if args.action == 'register':
        register(args.path)
    else:
        list_registry()


if __name__ == '__main__':
    main()
