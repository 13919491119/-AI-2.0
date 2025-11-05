#!/usr/bin/env python3
"""
Package a model artifact: compute sha256, write metadata JSON and optionally sign.
Usage: python3 tools/package_model.py --model-path ssq_ai_model_state.json --out-dir artifacts
"""
import argparse
import hashlib
import json
import os
from datetime import datetime


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model-path', required=True)
    p.add_argument('--out-dir', required=True)
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    model = args.model_path
    if not os.path.exists(model):
        print('model not found:', model)
        return
    digest = sha256_of_file(model)
    metadata = {
        'model_file': os.path.basename(model),
        'sha256': digest,
        'packaged_at': datetime.utcnow().isoformat() + 'Z'
    }
    meta_path = os.path.join(args.out_dir, 'metadata.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    # copy model into artifacts
    dst = os.path.join(args.out_dir, os.path.basename(model))
    with open(model, 'rb') as fr, open(dst, 'wb') as fw:
        fw.write(fr.read())
    print('Packaged:', dst)
    print('Wrote metadata:', meta_path)


if __name__ == '__main__':
    main()
